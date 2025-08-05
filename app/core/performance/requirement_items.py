"""Performance optimization utilities for requirement items."""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from datetime import datetime, timedelta

from app.domain.models.requirements import RequirementItem, RequirementItemStatus
from app.core.monitoring.requirement_items import monitor_performance

logger = logging.getLogger(__name__)


class RequirementItemsPerformanceOptimizer:
    """Performance optimization utilities for requirement items operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    @monitor_performance("analyze_query_performance")
    def analyze_query_performance(self) -> Dict[str, Any]:
        """Analyze query performance for requirement items table."""
        try:
            # Check if indexes exist
            index_query = text("""
                SELECT name, sql 
                FROM sqlite_master 
                WHERE type='index' AND tbl_name='requirement_items'
            """)
            
            indexes = self.db.execute(index_query).fetchall()
            
            # Get table statistics
            stats_query = text("""
                SELECT 
                    COUNT(*) as total_items,
                    COUNT(DISTINCT project_id) as unique_projects,
                    COUNT(CASE WHEN status = 'new' THEN 1 END) as new_items,
                    COUNT(CASE WHEN status = 'accepted' THEN 1 END) as accepted_items,
                    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_items
                FROM requirement_items
            """)
            
            stats = self.db.execute(stats_query).fetchone()
            
            # Check for potential performance issues
            performance_issues = []
            
            # Check if we have the required indexes
            required_indexes = [
                'idx_requirement_items_project_id',
                'idx_requirement_items_status', 
                'idx_requirement_items_project_status'
            ]
            
            existing_index_names = [idx[0] for idx in indexes if idx[0]]
            missing_indexes = [idx for idx in required_indexes if idx not in existing_index_names]
            
            if missing_indexes:
                performance_issues.append(f"Missing indexes: {missing_indexes}")
            
            # Check for large projects that might need optimization
            large_projects_query = text("""
                SELECT project_id, COUNT(*) as item_count
                FROM requirement_items 
                GROUP BY project_id 
                HAVING COUNT(*) > 100
                ORDER BY item_count DESC
            """)
            
            large_projects = self.db.execute(large_projects_query).fetchall()
            
            if large_projects:
                performance_issues.append(f"Large projects detected: {len(large_projects)} projects with >100 items")
            
            return {
                "indexes": [{"name": idx[0], "sql": idx[1]} for idx in indexes],
                "statistics": {
                    "total_items": stats[0] if stats else 0,
                    "unique_projects": stats[1] if stats else 0,
                    "new_items": stats[2] if stats else 0,
                    "accepted_items": stats[3] if stats else 0,
                    "rejected_items": stats[4] if stats else 0
                },
                "large_projects": [{"project_id": p[0], "item_count": p[1]} for p in large_projects],
                "performance_issues": performance_issues,
                "recommendations": self._get_performance_recommendations(stats, large_projects, missing_indexes)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing query performance: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    def _get_performance_recommendations(self, stats, large_projects, missing_indexes) -> List[str]:
        """Generate performance recommendations based on analysis."""
        recommendations = []
        
        if missing_indexes:
            recommendations.append("Create missing database indexes to improve query performance")
        
        if large_projects:
            recommendations.append("Consider implementing pagination for projects with many requirement items")
            recommendations.append("Monitor query performance for large projects")
        
        if stats and stats[0] > 10000:  # More than 10k total items
            recommendations.append("Consider implementing database partitioning for very large datasets")
            recommendations.append("Implement query result caching for frequently accessed data")
        
        if not recommendations:
            recommendations.append("Performance appears optimal for current data size")
        
        return recommendations
    
    @monitor_performance("optimize_project_queries")
    def optimize_project_queries(self, project_id: str) -> Dict[str, Any]:
        """Optimize queries for a specific project."""
        try:
            # Analyze query patterns for this project
            project_stats_query = text("""
                SELECT 
                    COUNT(*) as total_items,
                    COUNT(CASE WHEN status = 'new' THEN 1 END) as new_items,
                    COUNT(CASE WHEN status = 'accepted' THEN 1 END) as accepted_items,
                    COUNT(CASE WHEN status = 'rejected' THEN 1 END) as rejected_items,
                    COUNT(CASE WHEN priority = 'critical' THEN 1 END) as critical_items,
                    COUNT(CASE WHEN priority = 'high' THEN 1 END) as high_items,
                    MIN(created_at) as oldest_item,
                    MAX(updated_at) as latest_update
                FROM requirement_items 
                WHERE project_id = :project_id
            """)
            
            stats = self.db.execute(project_stats_query, {"project_id": project_id}).fetchone()
            
            if not stats or stats[0] == 0:
                return {"project_id": project_id, "message": "No items found for this project"}
            
            # Check for optimization opportunities
            optimizations = []
            
            if stats[0] > 500:  # Large project
                optimizations.append("Consider using pagination with smaller page sizes")
                optimizations.append("Implement status-based filtering to reduce result sets")
            
            if stats[1] > stats[2] + stats[3]:  # Many new items
                optimizations.append("High number of new items - consider bulk status updates")
            
            return {
                "project_id": project_id,
                "statistics": {
                    "total_items": stats[0],
                    "new_items": stats[1],
                    "accepted_items": stats[2],
                    "rejected_items": stats[3],
                    "critical_items": stats[4],
                    "high_items": stats[5],
                    "oldest_item": stats[6],
                    "latest_update": stats[7]
                },
                "optimizations": optimizations
            }
            
        except Exception as e:
            logger.error(f"Error optimizing project queries for {project_id}: {str(e)}", exc_info=True)
            return {"project_id": project_id, "error": str(e)}
    
    @monitor_performance("cleanup_old_data")
    def cleanup_old_data(self, days_old: int = 365) -> Dict[str, Any]:
        """Clean up old requirement items data (for maintenance)."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Find old items that might be candidates for archival
            old_items_query = text("""
                SELECT project_id, COUNT(*) as old_item_count
                FROM requirement_items 
                WHERE updated_at < :cutoff_date 
                AND status IN ('rejected', 'accepted')
                GROUP BY project_id
                ORDER BY old_item_count DESC
            """)
            
            old_items = self.db.execute(old_items_query, {"cutoff_date": cutoff_date}).fetchall()
            
            total_old_items = sum(item[1] for item in old_items)
            
            return {
                "cutoff_date": cutoff_date.isoformat(),
                "projects_with_old_items": len(old_items),
                "total_old_items": total_old_items,
                "old_items_by_project": [
                    {"project_id": item[0], "count": item[1]} 
                    for item in old_items
                ],
                "recommendations": [
                    "Consider archiving old accepted/rejected items to improve performance",
                    "Implement data retention policies for requirement items",
                    "Monitor database size growth over time"
                ] if total_old_items > 1000 else ["No cleanup needed at this time"]
            }
            
        except Exception as e:
            logger.error(f"Error during cleanup analysis: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    @monitor_performance("create_performance_indexes")
    def create_performance_indexes(self) -> Dict[str, Any]:
        """Create additional performance indexes if they don't exist."""
        try:
            indexes_created = []
            indexes_skipped = []
            
            # List of indexes to create
            indexes_to_create = [
                {
                    "name": "idx_requirement_items_priority",
                    "sql": "CREATE INDEX IF NOT EXISTS idx_requirement_items_priority ON requirement_items (priority)"
                },
                {
                    "name": "idx_requirement_items_created_at",
                    "sql": "CREATE INDEX IF NOT EXISTS idx_requirement_items_created_at ON requirement_items (created_at DESC)"
                },
                {
                    "name": "idx_requirement_items_updated_at", 
                    "sql": "CREATE INDEX IF NOT EXISTS idx_requirement_items_updated_at ON requirement_items (updated_at DESC)"
                },
                {
                    "name": "idx_requirement_items_title_search",
                    "sql": "CREATE INDEX IF NOT EXISTS idx_requirement_items_title_search ON requirement_items (project_id, title)"
                }
            ]
            
            for index in indexes_to_create:
                try:
                    self.db.execute(text(index["sql"]))
                    indexes_created.append(index["name"])
                    logger.info(f"Created performance index: {index['name']}")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        indexes_skipped.append(index["name"])
                    else:
                        logger.error(f"Failed to create index {index['name']}: {str(e)}")
                        raise
            
            self.db.commit()
            
            return {
                "indexes_created": indexes_created,
                "indexes_skipped": indexes_skipped,
                "message": f"Created {len(indexes_created)} new indexes, skipped {len(indexes_skipped)} existing indexes"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating performance indexes: {str(e)}", exc_info=True)
            return {"error": str(e)}
    
    @monitor_performance("vacuum_database")
    def vacuum_database(self) -> Dict[str, Any]:
        """Vacuum the database to optimize storage and performance."""
        try:
            # Get database size before vacuum
            size_before_query = text("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            size_before = self.db.execute(size_before_query).scalar()
            
            # Perform vacuum
            self.db.execute(text("VACUUM"))
            
            # Get database size after vacuum
            size_after = self.db.execute(size_before_query).scalar()
            
            space_saved = size_before - size_after
            
            logger.info(f"Database vacuum completed. Space saved: {space_saved} bytes")
            
            return {
                "size_before_bytes": size_before,
                "size_after_bytes": size_after,
                "space_saved_bytes": space_saved,
                "space_saved_mb": round(space_saved / (1024 * 1024), 2),
                "message": "Database vacuum completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Error during database vacuum: {str(e)}", exc_info=True)
            return {"error": str(e)}


def get_performance_optimizer(db: Session) -> RequirementItemsPerformanceOptimizer:
    """Get a performance optimizer instance."""
    return RequirementItemsPerformanceOptimizer(db)