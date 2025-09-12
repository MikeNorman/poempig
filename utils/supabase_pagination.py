#!/usr/bin/env python3
"""
Supabase Pagination Utility

This module provides utilities for handling Supabase's 1000 record limit
by implementing proper pagination strategies.
"""

import time
from typing import List, Dict, Any, Optional, Generator, Callable
from supabase import Client
import logging

logger = logging.getLogger(__name__)

class SupabasePagination:
    """Utility class for handling Supabase pagination"""
    
    def __init__(self, supabase_client: Client, table_name: str):
        self.client = supabase_client
        self.table_name = table_name
        self.page_size = 1000  # Supabase's maximum limit
    
    def get_all_records(
        self, 
        select_fields: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Get all records from a Supabase table using pagination.
        
        Args:
            select_fields: Fields to select (default: "*")
            filters: Dictionary of filters to apply
            order_by: Field to order by
            order_desc: Whether to order in descending order
            progress_callback: Optional callback for progress updates (current_count, total_count)
            
        Yields:
            List[Dict]: Pages of records
        """
        offset = 0
        total_retrieved = 0
        
        while True:
            try:
                # Build the query
                query = self.client.table(self.table_name).select(select_fields)
                
                # Apply filters
                if filters:
                    for field, value in filters.items():
                        if field.endswith('_eq'):
                            query = query.eq(field[:-3], value)
                        elif field.endswith('_neq'):
                            query = query.neq(field[:-4], value)
                        elif field.endswith('_gt'):
                            query = query.gt(field[:-3], value)
                        elif field.endswith('_gte'):
                            query = query.gte(field[:-4], value)
                        elif field.endswith('_lt'):
                            query = query.lt(field[:-3], value)
                        elif field.endswith('_lte'):
                            query = query.lte(field[:-4], value)
                        elif field.endswith('_like'):
                            query = query.like(field[:-5], value)
                        elif field.endswith('_ilike'):
                            query = query.ilike(field[:-6], value)
                        elif field.endswith('_in'):
                            query = query.in_(field[:-3], value)
                        elif field.endswith('_is'):
                            query = query.is_(field[:-3], value)
                        elif field.endswith('_not_is'):
                            query = query.not_.is_(field[:-8], value)
                        else:
                            # Default to equality
                            query = query.eq(field, value)
                
                # Apply ordering
                if order_by:
                    query = query.order(order_by, desc=order_desc)
                
                # Apply pagination
                query = query.range(offset, offset + self.page_size - 1)
                
                # Execute query
                result = query.execute()
                
                if not result.data or len(result.data) == 0:
                    logger.info("No more records found")
                    break
                
                # Update counters
                total_retrieved += len(result.data)
                
                # Call progress callback if provided
                if progress_callback:
                    progress_callback(total_retrieved, None)  # We don't know total count
                
                logger.info(f"Retrieved {len(result.data)} records (total: {total_retrieved})")
                
                # Yield the page
                yield result.data
                
                # Check if we got fewer records than requested (last page)
                if len(result.data) < self.page_size:
                    logger.info("Last page reached")
                    break
                
                # Update offset for next iteration
                offset += self.page_size
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error retrieving records at offset {offset}: {e}")
                raise
    
    def get_all_records_list(
        self, 
        select_fields: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all records as a single list (loads everything into memory).
        
        Args:
            select_fields: Fields to select (default: "*")
            filters: Dictionary of filters to apply
            order_by: Field to order by
            order_desc: Whether to order in descending order
            progress_callback: Optional callback for progress updates
            
        Returns:
            List[Dict]: All records
        """
        all_records = []
        
        for page in self.get_all_records(select_fields, filters, order_by, order_desc, progress_callback):
            all_records.extend(page)
        
        return all_records
    
    def count_records(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count total records in the table.
        
        Args:
            filters: Dictionary of filters to apply
            
        Returns:
            int: Total count of records
        """
        try:
            query = self.client.table(self.table_name).select('id', count='exact')
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if field.endswith('_eq'):
                        query = query.eq(field[:-3], value)
                    elif field.endswith('_neq'):
                        query = query.neq(field[:-4], value)
                    elif field.endswith('_gt'):
                        query = query.gt(field[:-3], value)
                    elif field.endswith('_gte'):
                        query = query.gte(field[:-4], value)
                    elif field.endswith('_lt'):
                        query = query.lt(field[:-3], value)
                    elif field.endswith('_lte'):
                        query = query.lte(field[:-4], value)
                    elif field.endswith('_like'):
                        query = query.like(field[:-5], value)
                    elif field.endswith('_ilike'):
                        query = query.ilike(field[:-6], value)
                    elif field.endswith('_in'):
                        query = query.in_(field[:-3], value)
                    elif field.endswith('_is'):
                        query = query.is_(field[:-3], value)
                    elif field.endswith('_not_is'):
                        query = query.not_.is_(field[:-8], value)
                    else:
                        query = query.eq(field, value)
            
            result = query.execute()
            return result.count or 0
            
        except Exception as e:
            logger.error(f"Error counting records: {e}")
            return 0

def create_pagination_client(supabase_client: Client, table_name: str) -> SupabasePagination:
    """Factory function to create a pagination client"""
    return SupabasePagination(supabase_client, table_name)

# Example usage
def example_usage():
    """Example of how to use the pagination utility"""
    from supabase import create_client, Client
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    # Initialize Supabase client
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )
    
    # Create pagination client
    pagination = create_pagination_client(supabase, "poems")
    
    # Example 1: Get all records as a generator (memory efficient)
    print("Getting all poems with pagination...")
    total_count = 0
    for page in pagination.get_all_records(select_fields="id, title, author"):
        total_count += len(page)
        print(f"Retrieved page with {len(page)} poems (total so far: {total_count})")
    
    print(f"Total poems retrieved: {total_count}")
    
    # Example 2: Get all records as a list (loads everything into memory)
    print("\nGetting all poems as a list...")
    all_poems = pagination.get_all_records_list(select_fields="id, title, author")
    print(f"Total poems in list: {len(all_poems)}")
    
    # Example 3: Get records with filters
    print("\nGetting poems by specific author...")
    author_poems = pagination.get_all_records_list(
        select_fields="id, title, author",
        filters={"author_eq": "William Shakespeare"}
    )
    print(f"Shakespeare poems: {len(author_poems)}")
    
    # Example 4: Count records
    print("\nCounting total poems...")
    total_count = pagination.count_records()
    print(f"Total poems in database: {total_count}")

if __name__ == "__main__":
    example_usage()
