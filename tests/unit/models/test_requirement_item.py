"""Unit tests for RequirementItem model."""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.core.database import Base
from app.domain.models.requirements import (
    RequirementItem, 
    RequirementItemStatus, 
    RequirementItemPriority
)
from app.domain.models import Project, ProjectState


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_project(db_session):
    """Create a sample project for testing."""
    project = Project(
        id="test-project-1",
        name="Test Project",
        description="A test project",
        state=ProjectState.active
    )
    db_session.add(project)
    db_session.commit()
    return project


class TestRequirementItemStatus:
    """Test RequirementItemStatus enum."""
    
    def test_enum_values(self):
        """Test that enum has correct values."""
        assert RequirementItemStatus.new.value == "new"
        assert RequirementItemStatus.accepted.value == "accepted"
        assert RequirementItemStatus.rejected.value == "rejected"
    
    def test_enum_members(self):
        """Test that enum has correct members."""
        expected_members = {"new", "accepted", "rejected"}
        actual_members = {status.value for status in RequirementItemStatus}
        assert actual_members == expected_members


class TestRequirementItemPriority:
    """Test RequirementItemPriority enum."""
    
    def test_enum_values(self):
        """Test that enum has correct values."""
        assert RequirementItemPriority.low.value == "low"
        assert RequirementItemPriority.medium.value == "medium"
        assert RequirementItemPriority.high.value == "high"
        assert RequirementItemPriority.critical.value == "critical"
    
    def test_enum_members(self):
        """Test that enum has correct members."""
        expected_members = {"low", "medium", "high", "critical"}
        actual_members = {priority.value for priority in RequirementItemPriority}
        assert actual_members == expected_members


class TestRequirementItem:
    """Test RequirementItem model."""
    
    def test_create_requirement_item(self, db_session, sample_project):
        """Test creating a requirement item."""
        item = RequirementItem(
            project_id=sample_project.id,
            title="Test Requirement",
            description="This is a test requirement item"
        )
        db_session.add(item)
        db_session.commit()
        
        assert item.id is not None
        assert item.project_id == sample_project.id
        assert item.title == "Test Requirement"
        assert item.description == "This is a test requirement item"
        assert item.priority == RequirementItemPriority.medium  # Default
        assert item.status == RequirementItemStatus.new  # Default
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.updated_at, datetime)
    
    def test_create_requirement_item_with_custom_values(self, db_session, sample_project):
        """Test creating a requirement item with custom priority and status."""
        item = RequirementItem(
            project_id=sample_project.id,
            title="High Priority Requirement",
            description="This is a high priority requirement",
            priority=RequirementItemPriority.high,
            status=RequirementItemStatus.accepted
        )
        db_session.add(item)
        db_session.commit()
        
        assert item.priority == RequirementItemPriority.high
        assert item.status == RequirementItemStatus.accepted
    
    def test_requirement_item_project_relationship(self, db_session, sample_project):
        """Test the relationship between RequirementItem and Project."""
        item = RequirementItem(
            project_id=sample_project.id,
            title="Test Requirement",
            description="This is a test requirement item"
        )
        db_session.add(item)
        db_session.commit()
        
        # Test forward relationship
        assert item.project == sample_project
        
        # Test backward relationship
        db_session.refresh(sample_project)
        assert item in sample_project.requirement_items
    
    def test_requirement_item_without_project_id_fails(self, db_session):
        """Test that creating a requirement item without project_id fails."""
        item = RequirementItem(
            title="Test Requirement",
            description="This is a test requirement item"
        )
        db_session.add(item)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_requirement_item_with_invalid_project_id_fails(self, db_session):
        """Test that creating a requirement item with invalid project_id fails."""
        item = RequirementItem(
            project_id="non-existent-project",
            title="Test Requirement",
            description="This is a test requirement item"
        )
        db_session.add(item)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_requirement_item_without_title_fails(self, db_session, sample_project):
        """Test that creating a requirement item without title fails."""
        item = RequirementItem(
            project_id=sample_project.id,
            description="This is a test requirement item"
        )
        db_session.add(item)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_requirement_item_without_description_fails(self, db_session, sample_project):
        """Test that creating a requirement item without description fails."""
        item = RequirementItem(
            project_id=sample_project.id,
            title="Test Requirement"
        )
        db_session.add(item)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_requirement_item_title_max_length(self, db_session, sample_project):
        """Test that requirement item title respects max length constraint."""
        # Create a title that's exactly 500 characters
        long_title = "A" * 500
        item = RequirementItem(
            project_id=sample_project.id,
            title=long_title,
            description="This is a test requirement item"
        )
        db_session.add(item)
        db_session.commit()
        
        assert item.title == long_title
        assert len(item.title) == 500
    
    def test_requirement_item_cascade_delete(self, db_session, sample_project):
        """Test that requirement items are deleted when project is deleted."""
        item = RequirementItem(
            project_id=sample_project.id,
            title="Test Requirement",
            description="This is a test requirement item"
        )
        db_session.add(item)
        db_session.commit()
        
        item_id = item.id
        
        # Delete the project
        db_session.delete(sample_project)
        db_session.commit()
        
        # Verify the requirement item was also deleted
        deleted_item = db_session.query(RequirementItem).filter_by(id=item_id).first()
        assert deleted_item is None
    
    def test_requirement_item_updated_at_changes(self, db_session, sample_project):
        """Test that updated_at timestamp changes when item is modified."""
        item = RequirementItem(
            project_id=sample_project.id,
            title="Test Requirement",
            description="This is a test requirement item"
        )
        db_session.add(item)
        db_session.commit()
        
        original_updated_at = item.updated_at
        
        # Modify the item
        item.title = "Updated Test Requirement"
        db_session.commit()
        
        assert item.updated_at > original_updated_at
    
    def test_multiple_requirement_items_per_project(self, db_session, sample_project):
        """Test that a project can have multiple requirement items."""
        items = []
        for i in range(3):
            item = RequirementItem(
                project_id=sample_project.id,
                title=f"Test Requirement {i+1}",
                description=f"This is test requirement item {i+1}"
            )
            items.append(item)
            db_session.add(item)
        
        db_session.commit()
        
        # Verify all items were created
        for item in items:
            assert item.id is not None
        
        # Verify project has all items
        db_session.refresh(sample_project)
        assert len(sample_project.requirement_items) == 3
        
        # Verify all items belong to the project
        for item in items:
            assert item in sample_project.requirement_items