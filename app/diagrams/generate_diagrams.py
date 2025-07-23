from app.ollama_client import call_ollama
from app.logger import get_logger

logger = get_logger()

def generate_c4_diagram(sequence_diagram: str, c4_type: int):
    if c4_type not in (1, 2, 3):
        raise ValueError("Invalid c4_type. Use 1 (System Context), 2 (Container), or 3 (Component).")
    # Επιλογή prompt ανάλογα με το type
    match c4_type:
        case 1:
            c4_level = "System Context"
            instructions = get_instructions(c4_level)
            prompt_template = get_system_context_prompt(instructions)
        case 2:
            c4_level = "Container"
            instructions = get_instructions(c4_level)
            prompt_template = get_container_prompt(instructions)
        case 3:
            c4_level = "Component"
            instructions = get_instructions(c4_level)
            prompt_template = get_component_prompt(instructions)
        case _:
            return "Invalid c4_type. Use 1 (System Context), 2 (Container), or 3 (Component)."


    
    prompt = f"""
    {prompt_template}

## Input Sequence Diagram:
{sequence_diagram}


**Return the response strictly in JSON format with two fields:**
- diagram: the MermaidJS C4 diagram as a string (inside triple backticks).
- explanation: a short description of the design choices and mapping.

```json
{{
  "diagram": "Mermaidjs\nC4Component\ntitle Component diagram for Internet Banking System - API Application\n\nContainer(spa, \"Single Page Application\", \"javascript and angular\", \"Provides all the internet banking functionality to customers via their web browser.\")\nContainer(ma, \"Mobile App\", \"Xamarin\", \"Provides a limited subset to the internet banking functionality to customers via their mobile device.\")\nContainerDb(db, \"Database\", \"Relational Database Schema\", \"Stores user registration information, hashed authentication credentials, access logs, etc.\")\nSystem_Ext(mbs, \"Mainframe Banking System\", \"Stores all of the core banking information about customers, accounts, transactions, etc.\")\n\nContainer_Boundary(api, \"API Application\") {{\n    Component(sign, \"Sign In Controller\", \"MVC Rest Controller\", \"Allows users to sign in to the internet banking system\")\n    Component(accounts, \"Accounts Summary Controller\", \"MVC Rest Controller\", \"Provides customers with a summary of their bank accounts\")\n    Component(security, \"Security Component\", \"Spring Bean\", \"Provides functionality related to singing in, changing passwords, etc.\")\n    Component(mbsfacade, \"Mainframe Banking System Facade\", \"Spring Bean\", \"A facade onto the mainframe banking system.\")\n\n    Rel(sign, security, \"Uses\")\n    Rel(accounts, mbsfacade, \"Uses\")\n    Rel(security, db, \"Read & write to\", \"JDBC\")\n    Rel(mbsfacade, mbs, \"Uses\", \"XML/HTTPS\")\n}}\n\nRel_Back(spa, sign, \"Uses\", \"JSON/HTTPS\")\nRel(spa, accounts, \"Uses\", \"JSON/HTTPS\")\n\nRel(ma, sign, \"Uses\", \"JSON/HTTPS\")\nRel(ma, accounts, \"Uses\", \"JSON/HTTPS\")\n\nUpdateRelStyle(spa, sign, $offsetY=\"-40\")\nUpdateRelStyle(spa, accounts, $offsetX=\"40\", $offsetY=\"40\")\n\nUpdateRelStyle(ma, sign, $offsetX=\"-90\", $offsetY=\"40\")\nUpdateRelStyle(ma, accounts, $offsetY=\"-40\")\n\nUpdateRelStyle(sign, security, $offsetX=\"-160\", $offsetY=\"10\")\nUpdateRelStyle(accounts, mbsfacade, $offsetX=\"140\", $offsetY=\"10\")\nUpdateRelStyle(security, db, $offsetY=\"-40\")\nUpdateRelStyle(mbsfacade, mbs, $offsetY=\"-40\")\n",
  "explanation": "The diagram maps the sequence participants into C4 containers and components. The web browser (SPA) and mobile app (ma) are containers. The backend API app contains components like sign (Sign In Controller) and accounts (Accounts Summary Controller), using Spring beans like security and mbsfacade. Relationships are drawn between components and external systems, like the mainframe. UpdateRelStyle adjusts label positions for clarity."
}}
````
Do not include any additional text or commentary outside the JSON.
    """

    answer = call_ollama(prompt, prompt_key="")
    logger.info(answer)
    return answer

def get_instructions(c4_level: str):
    return f"""
You are an expert software architect specializing in system design and the C4 model.

Your task is to convert the provided MermaidJS sequence diagram into a **MermaidJS C4 {c4_level} diagram**.

## MermaidJS C4 Syntax Rules
You MUST use the following MermaidJS commands to construct the diagram. Do NOT use any other syntax.

    """

def get_container_prompt(instructions:str):
    return f"""
    {instructions}
    ```Mermaidjs
    C4Container
    title Container diagram for Internet Banking System

    System_Ext(email_system, "E-Mail System", "The internal Microsoft Exchange system", $tags="v1.0")
    Person(customer, Customer, "A customer of the bank, with personal bank accounts", $tags="v1.0")

    Container_Boundary(c1, "Internet Banking") {{
        Container(spa, "Single-Page App", "JavaScript, Angular", "Provides all the Internet banking functionality to customers via their web browser")
        Container_Ext(mobile_app, "Mobile App", "C#, Xamarin", "Provides a limited subset of the Internet banking functionality to customers via their mobile device")
        Container(web_app, "Web Application", "Java, Spring MVC", "Delivers the static content and the Internet banking SPA")
        ContainerDb(database, "Database", "SQL Database", "Stores user registration information, hashed auth credentials, access logs, etc.")
        ContainerDb_Ext(backend_api, "API Application", "Java, Docker Container", "Provides Internet banking functionality via API")

    }}

    System_Ext(banking_system, "Mainframe Banking System", "Stores all of the core banking information about customers, accounts, transactions, etc.")

    Rel(customer, web_app, "Uses", "HTTPS")
    UpdateRelStyle(customer, web_app, $offsetY="60", $offsetX="90")
    Rel(customer, spa, "Uses", "HTTPS")
    UpdateRelStyle(customer, spa, $offsetY="-40")
    Rel(customer, mobile_app, "Uses")
    UpdateRelStyle(customer, mobile_app, $offsetY="-30")

    Rel(web_app, spa, "Delivers")
    UpdateRelStyle(web_app, spa, $offsetX="130")
    Rel(spa, backend_api, "Uses", "async, JSON/HTTPS")
    Rel(mobile_app, backend_api, "Uses", "async, JSON/HTTPS")
    Rel_Back(database, backend_api, "Reads from and writes to", "sync, JDBC")

    Rel(email_system, customer, "Sends e-mails to")
    UpdateRelStyle(email_system, customer, $offsetX="-45")
    Rel(backend_api, email_system, "Sends e-mails using", "sync, SMTP")
    UpdateRelStyle(backend_api, email_system, $offsetY="-60")
    Rel(backend_api, banking_system, "Uses", "sync/async, XML/HTTPS")
    UpdateRelStyle(backend_api, banking_system, $offsetY="-50", $offsetX="-140")

    
    ```
    """


def get_system_context_prompt(instructions:str):
    return f"""
    {instructions}
    System Context Diagram sample
    ```Mermaidjs
    C4Context
      title System Context diagram for Internet Banking System
      Enterprise_Boundary(b0, "BankBoundary0") {{
        Person(customerA, "Banking Customer A", "A customer of the bank, with personal bank accounts.")
        Person(customerB, "Banking Customer B")
        Person_Ext(customerC, "Banking Customer C", "desc")

        Person(customerD, "Banking Customer D", "A customer of the bank, <br/> with personal bank accounts.")

        System(SystemAA, "Internet Banking System", "Allows customers to view information about their bank accounts, and make payments.")

        Enterprise_Boundary(b1, "BankBoundary") {{

          SystemDb_Ext(SystemE, "Mainframe Banking System", "Stores all of the core banking information about customers, accounts, transactions, etc.")

          System_Boundary(b2, "BankBoundary2") {{
            System(SystemA, "Banking System A")
            System(SystemB, "Banking System B", "A system of the bank, with personal bank accounts. next line.")
          }}

          System_Ext(SystemC, "E-mail system", "The internal Microsoft Exchange e-mail system.")
          SystemDb(SystemD, "Banking System D Database", "A system of the bank, with personal bank accounts.")

          Boundary(b3, "BankBoundary3", "boundary") {{
            SystemQueue(SystemF, "Banking System F Queue", "A system of the bank.")
            SystemQueue_Ext(SystemG, "Banking System G Queue", "A system of the bank, with personal bank accounts.")
          }}
        }}
      }}

      BiRel(customerA, SystemAA, "Uses")
      BiRel(SystemAA, SystemE, "Uses")
      Rel(SystemAA, SystemC, "Sends e-mails", "SMTP")
      Rel(SystemC, customerA, "Sends e-mails to")

      UpdateElementStyle(customerA, $fontColor="red", $bgColor="grey", $borderColor="red")
      UpdateRelStyle(customerA, SystemAA, $textColor="blue", $lineColor="blue", $offsetX="5")
      UpdateRelStyle(SystemAA, SystemE, $textColor="blue", $lineColor="blue", $offsetY="-10")
      UpdateRelStyle(SystemAA, SystemC, $textColor="blue", $lineColor="blue", $offsetY="-40", $offsetX="-50")
      UpdateRelStyle(SystemC, customerA, $textColor="red", $lineColor="red", $offsetX="-50", $offsetY="20")

      UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")


    ```
    """


def get_component_prompt(instructions:str):
    return f"""
    {instructions}
    C4Component sample
    ```Mermaidjs
    C4Component
    title Component diagram for Internet Banking System - API Application

    Container(spa, "Single Page Application", "javascript and angular", "Provides all the internet banking functionality to customers via their web browser.")
    Container(ma, "Mobile App", "Xamarin", "Provides a limited subset to the internet banking functionality to customers via their mobile device.")
    ContainerDb(db, "Database", "Relational Database Schema", "Stores user registration information, hashed authentication credentials, access logs, etc.")
    System_Ext(mbs, "Mainframe Banking System", "Stores all of the core banking information about customers, accounts, transactions, etc.")

    Container_Boundary(api, "API Application") {{
        Component(sign, "Sign In Controller", "MVC Rest Controller", "Allows users to sign in to the internet banking system")
        Component(accounts, "Accounts Summary Controller", "MVC Rest Controller", "Provides customers with a summary of their bank accounts")
        Component(security, "Security Component", "Spring Bean", "Provides functionality related to singing in, changing passwords, etc.")
        Component(mbsfacade, "Mainframe Banking System Facade", "Spring Bean", "A facade onto the mainframe banking system.")

        Rel(sign, security, "Uses")
        Rel(accounts, mbsfacade, "Uses")
        Rel(security, db, "Read & write to", "JDBC")
        Rel(mbsfacade, mbs, "Uses", "XML/HTTPS")
    }}

    Rel_Back(spa, sign, "Uses", "JSON/HTTPS")
    Rel(spa, accounts, "Uses", "JSON/HTTPS")

    Rel(ma, sign, "Uses", "JSON/HTTPS")
    Rel(ma, accounts, "Uses", "JSON/HTTPS")

    UpdateRelStyle(spa, sign, $offsetY="-40")
    UpdateRelStyle(spa, accounts, $offsetX="40", $offsetY="40")

    UpdateRelStyle(ma, sign, $offsetX="-90", $offsetY="40")
    UpdateRelStyle(ma, accounts, $offsetY="-40")

        UpdateRelStyle(sign, security, $offsetX="-160", $offsetY="10")
        UpdateRelStyle(accounts, mbsfacade, $offsetX="140", $offsetY="10")
        UpdateRelStyle(security, db, $offsetY="-40")
        UpdateRelStyle(mbsfacade, mbs, $offsetY="-40")
    ```

    """

