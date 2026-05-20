"""
Baserow Database Client for Pinterest Growth Agent

This module provides a complete database layer using Baserow API
instead of SQLite, enabling cloud-based data storage and multi-server access.
"""

import os
import json
import logging
import httpx
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from src.models import Keyword, Trend, Pin, EngagementData

logger = logging.getLogger(__name__)


class BaserowClient:
    """Client for interacting with Baserow API."""
    
    def __init__(self, token: str, database_id: str, url: str = "https://api.baserow.io"):
        self.token = token
        self.database_id = database_id
        self.base_url = url.rstrip('/')
        self.headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json"
        }
        self._table_cache: Dict[str, int] = {}
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make HTTP request to Baserow API."""
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
    
    async def get_table_id(self, table_name: str) -> int:
        """Get table ID by name, caching result."""
        if table_name in self._table_cache:
            return self._table_cache[table_name]
        
        tables = await self._request("GET", f"/api/database/tables/")
        for table in tables.get("results", []):
            if table["name"].lower() == table_name.lower():
                self._table_cache[table_name] = table["id"]
                return table["id"]
        
        raise ValueError(f"Table '{table_name}' not found in database")
    
    async def list_rows(self, table_name: str, filters: Optional[Dict] = None, limit: int = 100) -> List[dict]:
        """List rows from a table with optional filters."""
        table_id = await self.get_table_id(table_name)
        params = {"limit": limit}
        
        # Add filters if provided (Baserow filter format: field__lookup=value)
        if filters:
            params.update(filters)
        
        result = await self._request("GET", f"/api/database/rows/table/{table_id}/", params=params)
        return result.get("results", [])
    
    async def create_row(self, table_name: str, data: Dict[str, Any]) -> dict:
        """Create a new row in a table."""
        table_id = await self.get_table_id(table_name)
        return await self._request("POST", f"/api/database/rows/table/{table_id}/", json=data)
    
    async def update_row(self, table_name: str, row_id: int, data: Dict[str, Any]) -> dict:
        """Update an existing row."""
        table_id = await self.get_table_id(table_name)
        return await self._request("PATCH", f"/api/database/rows/table/{table_id}/{row_id}/", json=data)
    
    async def delete_row(self, table_name: str, row_id: int) -> None:
        """Delete a row."""
        table_id = await self.get_table_id(table_name)
        await self._request("DELETE", f"/api/database/rows/table/{table_id}/{row_id}/")
    
    async def search_rows(self, table_name: str, field_name: str, value: str) -> List[dict]:
        """Search for rows where a field matches a value."""
        table_id = await self.get_table_id(table_name)
        # Baserow uses field__contains for partial match
        result = await self._request(
            "GET", 
            f"/api/database/rows/table/{table_id}/",
            params={f"{field_name}__contains": value, "limit": 100}
        )
        return result.get("results", [])


class BaserowDatabase:
    """Database layer using Baserow API - drop-in replacement for SQLite Database class."""
    
    # Table name mappings (Baserow table names should match these)
    TABLE_KEYWORDS = "keywords"
    TABLE_TRENDS = "trends"
    TABLE_PINS = "pins"
    TABLE_ENGAGEMENT = "engagement"
    TABLE_AGENT_LOG = "agent_log"
    TABLE_SCRAPER_HEALTH = "scraper_health"
    TABLE_DIAGNOSTIC_REPORTS = "diagnostic_reports"
    
    def __init__(self, db_path: str = "data/pga.db"):
        """Initialize Baserow connection from environment variables."""
        self.baserow_url = os.getenv("BASEROW_URL", "https://api.baserow.io")
        self.baserow_token = os.getenv("BASEROW_TOKEN")
        self.baserow_database_id = os.getenv("BASEROW_DATABASE_ID")
        
        if not self.baserow_token or not self.baserow_database_id:
            logger.warning("Baserow credentials not found, falling back to SQLite")
            self.use_baserow = False
            # Fall back to SQLite
            from src.store.database import Database as SQLiteDatabase
            self.sqlite_db = SQLiteDatabase(db_path)
        else:
            self.use_baserow = True
            self.client = BaserowClient(
                token=self.baserow_token,
                database_id=self.baserow_database_id,
                url=self.baserow_url
            )
            self._table_cache = {}
    
    async def _get_field_mappings(self, table_name: str) -> Dict[str, str]:
        """Get field name to ID mappings for a table."""
        if not self.use_baserow:
            return {}
        
        if table_name in self._table_cache:
            return self._table_cache[table_name]
        
        try:
            table_id = await self.client.get_table_id(table_name)
            fields = await self.client._request("GET", f"/api/database/fields/table/{table_id}/")
            
            mapping = {}
            for field in fields.get("results", []):
                mapping[field["name"].lower().replace(" ", "_")] = field["id"]
            
            self._table_cache[table_name] = mapping
            return mapping
        except Exception as e:
            logger.error(f"Failed to get field mappings for {table_name}: {e}")
            return {}
    
    def initialize(self) -> None:
        """Initialize database - for Baserow this validates connection."""
        if not self.use_baserow:
            self.sqlite_db.initialize()
            return
        
        logger.info("Using Baserow cloud database")
        logger.info(f"Database ID: {self.baserow_database_id}")
    
    def _connect(self):
        """Compatibility method - returns self for Baserow."""
        return self
    
    def close(self) -> None:
        """Close connection - no-op for Baserow (HTTP is stateless)."""
        pass
    
    # Keyword operations
    async def upsert_keyword_async(self, keyword: Keyword) -> None:
        """Upsert a keyword to Baserow."""
        if not self.use_baserow:
            self.sqlite_db.upsert_keyword(keyword)
            return
        
        try:
            # Search for existing
            rows = await self.client.search_rows(self.TABLE_KEYWORDS, "term", keyword.term)
            
            data = {
                "term": keyword.term,
                "suggestion_rank": keyword.suggestion_rank,
                "related_terms": json.dumps(keyword.related_terms),
                "source": keyword.source,
                "performance_score": keyword.performance_score,
                "discovered_at": keyword.discovered_at.isoformat() if keyword.discovered_at else datetime.now(timezone.utc).isoformat()
            }
            
            if rows:
                # Update existing
                await self.client.update_row(self.TABLE_KEYWORDS, rows[0]["id"], data)
            else:
                # Create new
                await self.client.create_row(self.TABLE_KEYWORDS, data)
        except Exception as e:
            logger.error(f"Failed to upsert keyword: {e}")
    
    def upsert_keyword(self, keyword: Keyword) -> None:
        """Synchronous wrapper for upsert_keyword_async."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(self.upsert_keyword_async(keyword))
    
    async def get_top_keywords_async(self, limit: int = 20) -> List[Keyword]:
        """Get top keywords from Baserow."""
        if not self.use_baserow:
            return self.sqlite_db.get_top_keywords(limit)
        
        try:
            rows = await self.client.list_rows(self.TABLE_KEYWORDS, limit=limit)
            keywords = []
            for row in rows:
                try:
                    related = json.loads(row.get("related_terms", "[]")) if row.get("related_terms") else []
                    discovered = datetime.fromisoformat(row["discovered_at"]) if row.get("discovered_at") else datetime.now(timezone.utc)
                    
                    keywords.append(Keyword(
                        term=row.get("term", ""),
                        suggestion_rank=int(row.get("suggestion_rank", 0)),
                        related_terms=related,
                        source=row.get("source", "autosuggest"),
                        performance_score=float(row.get("performance_score", 0.0)),
                        discovered_at=discovered
                    ))
                except Exception as e:
                    logger.warning(f"Failed to parse keyword row: {e}")
            
            # Sort by performance score
            keywords.sort(key=lambda k: (-k.performance_score, k.suggestion_rank))
            return keywords[:limit]
        except Exception as e:
            logger.error(f"Failed to get keywords: {e}")
            return []
    
    def get_top_keywords(self, limit: int = 20) -> List[Keyword]:
        """Synchronous wrapper."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.get_top_keywords_async(limit))
    
    # Pin operations
    async def insert_pin_async(self, pin: Pin) -> int:
        """Insert a pin to Baserow."""
        if not self.use_baserow:
            return self.sqlite_db.insert_pin(pin)
        
        try:
            data = {
                "image_path": pin.image_path,
                "image_hash": pin.image_hash,
                "title": pin.title,
                "description": pin.description,
                "alt_text": pin.alt_text,
                "target_keyword": pin.target_keyword,
                "board_name": pin.board_name,
                "content_type": pin.content_type,
                "status": pin.status,
                "scheduled_at": pin.scheduled_at.isoformat() if pin.scheduled_at else None,
                "created_at": pin.created_at.isoformat() if pin.created_at else datetime.now(timezone.utc).isoformat()
            }
            
            result = await self.client.create_row(self.TABLE_PINS, data)
            return result.get("id", 0)
        except Exception as e:
            logger.error(f"Failed to insert pin: {e}")
            return 0
    
    def insert_pin(self, pin: Pin) -> int:
        """Synchronous wrapper."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.insert_pin_async(pin))
    
    async def get_pending_pins_async(self) -> List[Pin]:
        """Get pending pins from Baserow."""
        if not self.use_baserow:
            return self.sqlite_db.get_pending_pins()
        
        try:
            rows = await self.client.list_rows(self.TABLE_PINS, limit=100)
            pins = []
            for row in rows:
                if row.get("status") == "pending":
                    try:
                        scheduled = None
                        if row.get("scheduled_at"):
                            scheduled = datetime.fromisoformat(row["scheduled_at"])
                        
                        created = datetime.fromisoformat(row["created_at"]) if row.get("created_at") else datetime.now(timezone.utc)
                        
                        pins.append(Pin(
                            id=row.get("id", 0),
                            image_path=row.get("image_path", ""),
                            image_hash=row.get("image_hash", ""),
                            title=row.get("title", ""),
                            description=row.get("description", ""),
                            alt_text=row.get("alt_text", ""),
                            target_keyword=row.get("target_keyword", ""),
                            board_name=row.get("board_name", ""),
                            content_type=row.get("content_type", "seo"),
                            status=row.get("status", "pending"),
                            scheduled_at=scheduled,
                            posted_at=None,
                            pinterest_url=row.get("pinterest_url", ""),
                            created_at=created
                        ))
                    except Exception as e:
                        logger.warning(f"Failed to parse pin row: {e}")
            
            return pins
        except Exception as e:
            logger.error(f"Failed to get pending pins: {e}")
            return []
    
    def get_pending_pins(self) -> List[Pin]:
        """Synchronous wrapper."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.get_pending_pins_async())
    
    # Log operations
    async def log_action_async(self, action: str, details: dict) -> None:
        """Log an action to Baserow."""
        if not self.use_baserow:
            self.sqlite_db.log_action(action, details)
            return
        
        try:
            data = {
                "action": action,
                "details": json.dumps(details),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await self.client.create_row(self.TABLE_AGENT_LOG, data)
        except Exception as e:
            logger.error(f"Failed to log action: {e}")
    
    def log_action(self, action: str, details: dict) -> None:
        """Synchronous wrapper."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(self.log_action_async(action, details))
    
    # Additional methods can be added as needed...
    # For now, the most critical operations are implemented
    
    def hash_exists(self, image_hash: str) -> bool:
        """Check if an image hash exists."""
        if not self.use_baserow:
            return self.sqlite_db.hash_exists(image_hash)
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        async def check():
            rows = await self.client.search_rows(self.TABLE_PINS, "image_hash", image_hash)
            return len(rows) > 0
        
        return loop.run_until_complete(check())
    
    def update_pin_status(self, pin_id: int, status: str) -> None:
        """Update pin status."""
        if not self.use_baserow:
            self.sqlite_db.update_pin_status(pin_id, status)
            return
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        async def update():
            await self.client.update_row(self.TABLE_PINS, pin_id, {"status": status})
        
        loop.run_until_complete(update())
    
    def set_pin_url(self, pin_id: int, url: str) -> None:
        """Set pin URL."""
        if not self.use_baserow:
            self.sqlite_db.set_pin_url(pin_id, url)
            return
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        async def update():
            await self.client.update_row(self.TABLE_PINS, pin_id, {"pinterest_url": url})
        
        loop.run_until_complete(update())
    
    def get_recent_pins(self, days: int = 7) -> List[Pin]:
        """Get recent pins."""
        if not self.use_baserow:
            return self.sqlite_db.get_recent_pins(days)
        
        # For simplicity, get all pins and filter in memory
        # In production, you'd use Baserow's date filters
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        async def fetch():
            rows = await self.client.list_rows(self.TABLE_PINS, limit=100)
            pins = []
            cutoff = datetime.now(timezone.utc).timestamp() - (days * 24 * 3600)
            
            for row in rows:
                try:
                    created_str = row.get("created_at")
                    if created_str:
                        created = datetime.fromisoformat(created_str)
                        if created.timestamp() >= cutoff:
                            pins.append(Pin(
                                id=row.get("id", 0),
                                image_path=row.get("image_path", ""),
                                image_hash=row.get("image_hash", ""),
                                title=row.get("title", ""),
                                description=row.get("description", ""),
                                alt_text=row.get("alt_text", ""),
                                target_keyword=row.get("target_keyword", ""),
                                board_name=row.get("board_name", ""),
                                content_type=row.get("content_type", "seo"),
                                status=row.get("status", "pending"),
                                scheduled_at=None,
                                posted_at=None,
                                pinterest_url=row.get("pinterest_url", ""),
                                created_at=created
                            ))
                except Exception as e:
                    logger.warning(f"Failed to parse pin row: {e}")
            
            return pins
        
        return loop.run_until_complete(fetch())
    
    def update_keyword_score(self, term: str, score: float) -> None:
        """Update keyword performance score."""
        if not self.use_baserow:
            self.sqlite_db.update_keyword_score(term, score)
            return
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        async def update():
            rows = await self.client.search_rows(self.TABLE_KEYWORDS, "term", term)
            if rows:
                await self.client.update_row(self.TABLE_KEYWORDS, rows[0]["id"], {"performance_score": score})
        
        loop.run_until_complete(update())
    
    def insert_trend(self, trend: Trend) -> None:
        """Insert a trend."""
        if not self.use_baserow:
            self.sqlite_db.insert_trend(trend)
            return
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        async def insert():
            data = {
                "name": trend.name,
                "velocity": trend.velocity,
                "region": trend.region,
                "category": trend.category,
                "keywords": json.dumps(trend.keywords),
                "fetched_at": trend.fetched_at.isoformat() if trend.fetched_at else datetime.now(timezone.utc).isoformat()
            }
            await self.client.create_row(self.TABLE_TRENDS, data)
        
        loop.run_until_complete(insert())
    
    def get_recent_trends(self, hours: int = 24) -> List[Trend]:
        """Get recent trends."""
        if not self.use_baserow:
            return self.sqlite_db.get_recent_trends(hours)
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        async def fetch():
            rows = await self.client.list_rows(self.TABLE_TRENDS, limit=100)
            trends = []
            cutoff = datetime.now(timezone.utc).timestamp() - (hours * 3600)
            
            for row in rows:
                try:
                    fetched_str = row.get("fetched_at")
                    if fetched_str:
                        fetched = datetime.fromisoformat(fetched_str)
                        if fetched.timestamp() >= cutoff:
                            trends.append(Trend(
                                name=row.get("name", ""),
                                velocity=float(row.get("velocity", 0.0)),
                                region=row.get("region", ""),
                                category=row.get("category", ""),
                                keywords=json.loads(row.get("keywords", "[]")) if row.get("keywords") else [],
                                fetched_at=fetched
                            ))
                except Exception as e:
                    logger.warning(f"Failed to parse trend row: {e}")
            
            trends.sort(key=lambda t: -t.velocity)
            return trends
        
        return loop.run_until_complete(fetch())
    
    def insert_engagement(self, data: EngagementData) -> None:
        """Insert engagement data."""
        if not self.use_baserow:
            self.sqlite_db.insert_engagement(data)
            return
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        async def insert():
            row_data = {
                "pin_id": data.pin_id,
                "impressions": data.impressions,
                "saves": data.saves,
                "clicks": data.clicks,
                "ctr": data.ctr,
                "save_rate": data.save_rate,
                "scraped_at": data.scraped_at.isoformat() if data.scraped_at else datetime.now(timezone.utc).isoformat()
            }
            await self.client.create_row(self.TABLE_ENGAGEMENT, row_data)
        
        loop.run_until_complete(insert())
    
    def update_pin_posted(self, pin_id: int, status: str, url: str | None, log_action: str, log_details: dict) -> None:
        """Update pin as posted and log the action."""
        if not self.use_baserow:
            self.sqlite_db.update_pin_posted(pin_id, status, url, log_action, log_details)
            return
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        async def update():
            now = datetime.now(timezone.utc).isoformat()
            await self.client.update_row(self.TABLE_PINS, pin_id, {
                "status": status,
                "pinterest_url": url or "",
                "posted_at": now if status == "posted" else None
            })
            
            await self.log_action_async(log_action, log_details)
        
        loop.run_until_complete(update())
