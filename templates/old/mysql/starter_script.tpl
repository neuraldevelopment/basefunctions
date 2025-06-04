"""
=============================================================================
 Licensed Materials, Property of neuraldevelopment , Munich
 Project : {{ instance_name }}
 Copyright (c) by neuraldevelopment
 All rights reserved.
 Description:
 Database connection script for {{ db_type }} instance: {{ instance_name }}
=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
from typing import Dict, Any, Optional
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------
def get_database_connector() -> basefunctions.DatabaseConnector:
   """
   Get a configured database connector for {{ instance_name }}.
   
   Returns
   -------
   basefunctions.DatabaseConnector
       Configured {{ db_type }} connector instance
   """
   # Create BaseDatabaseHandler instance
   db_handler = basefunctions.BaseDatabaseHandler()
   
   # Connect to database instance (configuration must exist in ConfigHandler)
   connector = db_handler.connect_to_database("{{ instance_name }}")
   
   return connector


# Example usage
if __name__ == "__main__":
   # Get the database connector
   connector: basefunctions.DatabaseConnector = get_database_connector()
   
   # Test the connection
   if connector.is_connected():
       print(f"Successfully connected to {{ db_type }} database: {{ instance_name }}")
       
       # Example query
       try:
           # For MySQL, you can test with a simple query
           result: Optional[Dict[str, Any]] = connector.fetch_one("SELECT VERSION();")
           print(f"Database version: {result}")
           
           # Show current database
           db_result: Optional[Dict[str, Any]] = connector.fetch_one("SELECT DATABASE();")
           print(f"Current database: {db_result}")
       except Exception as e:
           print(f"Error executing test query: {e}")
       
       # Close connection
       connector.close()
   else:
       print("Failed to connect to database")
       