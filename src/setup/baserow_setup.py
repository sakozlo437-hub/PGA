"""
Модуль автоматической настройки базы данных Baserow.
Создает необходимые таблицы и поля при первом запуске.
"""

import os
import requests
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class BaserowSetup:
    """Класс для автоматического создания структуры БД в Baserow."""

    BASE_URL = "https://api.baserow.io/api"
    
    # Схема таблиц: {имя_таблицы: [список_полей]}
    # Типы полей Baserow: text, number, boolean, date, url, email, rating, etc.
    DATABASE_SCHEMA = {
        "keywords": [
            {"name": "keyword", "type": "text", "required": True},
            {"name": "volume", "type": "number"},
            {"name": "competition", "type": "text"},
            {"name": "category", "type": "text"},
            {"name": "created_at", "type": "date"},
            {"name": "updated_at", "type": "date"},
        ],
        "trends": [
            {"name": "trend_name", "type": "text", "required": True},
            {"name": "growth_rate", "type": "number"},
            {"name": "category", "type": "text"},
            {"name": "description", "type": "text"},
            {"name": "detected_at", "type": "date"},
        ],
        "pins": [
            {"name": "pin_id", "type": "text", "required": True},
            {"name": "image_url", "type": "url"},
            {"name": "description", "type": "text"},
            {"name": "link", "type": "url"},
            {"name": "board_name", "type": "text"},
            {"name": "created_at", "type": "date"},
        ],
        "engagement": [
            {"name": "pin_id", "type": "text", "required": True},
            {"name": "saves", "type": "number"},
            {"name": "clicks", "type": "number"},
            {"name": "impressions", "type": "number"},
            {"name": "engagement_rate", "type": "number"},
            {"name": "recorded_at", "type": "date"},
        ],
        "agent_log": [
            {"name": "timestamp", "type": "date", "required": True},
            {"name": "action", "type": "text"},
            {"name": "status", "type": "text"},  # success, error, warning, info
            {"name": "message", "type": "text"},
            {"name": "details", "type": "text"},
        ],
        "scraper_health": [
            {"name": "check_time", "type": "date", "required": True},
            {"name": "cpu_usage", "type": "number"},
            {"name": "memory_usage", "type": "number"},
            {"name": "status", "type": "text"},  # healthy, warning, critical
            {"name": "uptime_hours", "type": "number"},
            {"name": "last_error", "type": "text"},
        ],
        "diagnostic_reports": [
            {"name": "report_date", "type": "date", "required": True},
            {"name": "issues_found", "type": "number"},
            {"name": "recommendations", "type": "text"},
            {"name": "summary", "type": "text"},
            {"name": "severity", "type": "text"},  # low, medium, high, critical
        ],
    }

    def __init__(self, token: str, database_id: int):
        """
        Инициализация клиента Baserow.

        :param token: API токен Baserow
        :param database_id: ID базы данных в Baserow
        """
        self.token = token
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json",
        }

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Выполнение HTTP запроса к API Baserow."""
        url = f"{self.BASE_URL}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка запроса к Baserow: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Ответ сервера: {e.response.text}")
            raise

    def get_existing_tables(self) -> Dict[str, int]:
        """
        Получить список существующих таблиц в базе.

        :return: Словарь {имя_таблицы: id_таблицы}
        """
        print(f"🔍 Получение списка таблиц из базы {self.database_id}...")
        response = self._make_request("GET", f"/database/tables/?database={self.database_id}")
        
        tables = {}
        for table in response.get("results", []):
            tables[table["name"]] = table["id"]
        
        print(f"✅ Найдено таблиц: {len(tables)}")
        return tables

    def create_table(self, table_name: str) -> int:
        """
        Создать новую таблицу.

        :param table_name: Имя таблицы
        :return: ID созданной таблицы
        """
        print(f"📝 Создание таблицы '{table_name}'...")
        data = {
            "name": table_name,
            "database": self.database_id,
        }
        response = self._make_request("POST", "/database/tables/", data)
        table_id = response["id"]
        print(f"✅ Таблица '{table_name}' создана (ID: {table_id})")
        return table_id

    def get_existing_fields(self, table_id: int) -> Dict[str, int]:
        """
        Получить список существующих полей в таблице.

        :param table_id: ID таблицы
        :return: Словарь {имя_поля: id_поля}
        """
        response = self._make_request("GET", f"/database/fields/?table_id={table_id}")
        
        fields = {}
        for field in response.get("results", []):
            fields[field["name"]] = field["id"]
        
        return fields

    def create_field(self, table_id: int, field_config: Dict) -> int:
        """
        Создать новое поле в таблице.

        :param table_id: ID таблицы
        :param field_config: Конфигурация поля (name, type, required)
        :return: ID созданного поля
        """
        field_name = field_config["name"]
        field_type = field_config["type"]
        
        # Маппинг типов полей для Baserow API
        type_mapping = {
            "text": "SingleLineTextField",
            "number": "NumberField",
            "boolean": "BooleanField",
            "date": "DateField",
            "url": "UrlField",
            "email": "EmailField",
            "long_text": "LongTextField",
        }
        
        baserow_type = type_mapping.get(field_type, "SingleLineTextField")
        
        data = {
            "name": field_name,
            "type": baserow_type,
            "table": table_id,
        }
        
        # Добавляем дополнительные параметры если нужно
        if field_config.get("required"):
            data["required"] = True
        
        print(f"   └─ Создание поля '{field_name}' ({baserow_type})...")
        response = self._make_request("POST", "/database/fields/", data)
        field_id = response["id"]
        print(f"   ✅ Поле '{field_name}' создано (ID: {field_id})")
        return field_id

    def setup_database(self) -> Dict[str, Any]:
        """
        Основная функция настройки базы данных.
        Создает недостающие таблицы и поля.

        :return: Отчет о выполненных действиях
        """
        print("\n" + "="*60)
        print("🚀 НАЧАЛО НАСТРОЙКИ БАЗЫ ДАННЫХ BASEROW")
        print("="*60 + "\n")

        report = {
            "tables_created": [],
            "fields_created": [],
            "tables_skipped": [],
            "errors": [],
        }

        # Получаем существующие таблицы
        existing_tables = self.get_existing_tables()

        # Проходим по каждой таблице из схемы
        for table_name, fields_schema in self.DATABASE_SCHEMA.items():
            try:
                # Если таблица не существует - создаем
                if table_name not in existing_tables:
                    table_id = self.create_table(table_name)
                    report["tables_created"].append({"name": table_name, "id": table_id})
                else:
                    table_id = existing_tables[table_name]
                    report["tables_skipped"].append({"name": table_name, "id": table_id})
                    print(f"⏭️ Таблица '{table_name}' уже существует (ID: {table_id})")

                # Получаем существующие поля в таблице
                existing_fields = self.get_existing_fields(table_id)

                # Создаем недостающие поля
                for field_config in fields_schema:
                    field_name = field_config["name"]
                    if field_name not in existing_fields:
                        field_id = self.create_field(table_id, field_config)
                        report["fields_created"].append({
                            "table": table_name,
                            "field": field_name,
                            "id": field_id,
                        })
                    else:
                        print(f"   ⏭️ Поле '{field_name}' уже существует")

            except Exception as e:
                error_msg = f"Ошибка при настройке таблицы '{table_name}': {str(e)}"
                print(f"❌ {error_msg}")
                report["errors"].append(error_msg)

        # Вывод отчета
        self._print_report(report)
        
        return report

    def _print_report(self, report: Dict[str, Any]):
        """Вывод итогового отчета."""
        print("\n" + "="*60)
        print("📊 ОТЧЕТ О НАСТРОЙКЕ")
        print("="*60)
        
        print(f"\n✅ Таблиц создано: {len(report['tables_created'])}")
        for table in report["tables_created"]:
            print(f"   • {table['name']} (ID: {table['id']})")
        
        print(f"\n⏭️ Таблиц пропущено (уже существовали): {len(report['tables_skipped'])}")
        for table in report["tables_skipped"]:
            print(f"   • {table['name']} (ID: {table['id']})")
        
        print(f"\n✅ Полей создано: {len(report['fields_created'])}")
        for field in report["fields_created"][:10]:  # Показываем первые 10
            print(f"   • {field['table']}.{field['field']} (ID: {field['id']})")
        if len(report["fields_created"]) > 10:
            print(f"   ... и ещё {len(report['fields_created']) - 10} полей")
        
        if report["errors"]:
            print(f"\n❌ Ошибок: {len(report['errors'])}")
            for error in report["errors"]:
                print(f"   • {error}")
        else:
            print("\n🎉 Настройка завершена успешно!")
        
        print("="*60 + "\n")


def main():
    """Точка входа для настройки базы данных."""
    token = os.getenv("BASEROW_TOKEN")
    database_id = os.getenv("BASEROW_DATABASE_ID")

    if not token:
        print("❌ Ошибка: Не указан BASEROW_TOKEN в переменных окружения")
        return
    
    if not database_id:
        print("❌ Ошибка: Не указан BASEROW_DATABASE_ID в переменных окружения")
        return

    try:
        database_id_int = int(database_id)
    except ValueError:
        print(f"❌ Ошибка: BASEROW_DATABASE_ID должен быть числом, получено: {database_id}")
        return

    setup = BaserowSetup(token=token, database_id=database_id_int)
    setup.setup_database()


if __name__ == "__main__":
    main()
