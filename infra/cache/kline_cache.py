from __future__ import annotations

"""
模块名称：K 线缓存

功能描述：
    使用 SQLite 缓存 Stock Lab 标准 K 线数据。

设计原则：
    K 线唯一由以下字段确定：

        symbol + interval + timestamp

    SQLite 使用联合主键保证同一根 K 线不会重复。

    缓存负责：
        - K 线保存
        - K 线查询
        - 时间范围判断
        - 最新 K 线查询
        - 缓存删除

    缓存不负责：
        - 数据源请求
        - 数据源转换
        - 业务逻辑
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from common.constants import Interval
from core.models.stock.kline import Kline


class KlineCache:
    """
    K 线 SQLite 缓存。
    """

    def __init__(
        self,
        db_path: str | Path,
    ):
        self.db_path = Path(db_path)

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize()

    def get(
        self,
        symbol: str,
        interval: Interval,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int | None = None,
    ) -> list[Kline]:
        """
        查询指定时间范围内的 K 线。
        """

        sql = """
            SELECT
                symbol,
                interval,
                timestamp,
                open,
                high,
                low,
                close,
                volume,
                amount
            FROM kline
            WHERE symbol = ?
              AND interval = ?
        """

        parameters: list[object] = [
            symbol,
            interval.value,
        ]

        if start_time is not None:
            sql += """
                AND timestamp >= ?
            """

            parameters.append(start_time.isoformat())

        if end_time is not None:
            sql += """
                AND timestamp <= ?
            """

            parameters.append(end_time.isoformat())

        sql += """
            ORDER BY timestamp ASC
        """

        if limit is not None and limit > 0:
            sql += """
                LIMIT ?
            """

            parameters.append(limit)

        with self._connect() as connection:
            rows = connection.execute(
                sql,
                parameters,
            ).fetchall()

        return [self._row_to_kline(row) for row in rows]

    def get_many(
        self,
        symbols: list[str],
        interval: Interval,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int | None = None,
    ) -> dict[str, list[Kline]]:
        """
        批量查询 K 线。
        """

        result: dict[str, list[Kline]] = {}

        for symbol in symbols:
            result[symbol] = self.get(
                symbol=symbol,
                interval=interval,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
            )

        return result

    def contains_range(
        self,
        symbol: str,
        interval: Interval,
        start_time: datetime | None,
        end_time: datetime | None,
    ) -> bool:
        """
        判断缓存是否覆盖指定时间范围。

        注意：
            这里只判断缓存首尾范围。

            对日 K、周 K 等连续历史数据足够实用。
            后续如果需要严格检测中间交易日缺失，
            可以进一步增加交易日历检查。
        """

        cached_start, cached_end = self.get_range(
            symbol=symbol,
            interval=interval,
        )

        if cached_start is None or cached_end is None:
            return False

        if start_time is not None:
            if cached_start > start_time:
                return False

        if end_time is not None:
            if cached_end < end_time:
                return False

        return True

    def get_range(
        self,
        symbol: str,
        interval: Interval,
    ) -> tuple[datetime | None, datetime | None]:
        """
        获取缓存数据的时间范围。
        """

        sql = """
            SELECT
                MIN(timestamp),
                MAX(timestamp)
            FROM kline
            WHERE symbol = ?
              AND interval = ?
        """

        with self._connect() as connection:
            row = connection.execute(
                sql,
                (
                    symbol,
                    interval.value,
                ),
            ).fetchone()

        if row is None or row[0] is None:
            return None, None

        return (
            datetime.fromisoformat(row[0]),
            datetime.fromisoformat(row[1]),
        )

    def get_latest(
        self,
        symbol: str,
        interval: Interval,
    ) -> Kline | None:
        """
        获取最新一根 K 线。
        """

        sql = """
            SELECT
                symbol,
                interval,
                timestamp,
                open,
                high,
                low,
                close,
                volume,
                amount
            FROM kline
            WHERE symbol = ?
              AND interval = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """

        with self._connect() as connection:
            row = connection.execute(
                sql,
                (
                    symbol,
                    interval.value,
                ),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_kline(row)

    def save(
        self,
        klines: list[Kline],
    ) -> None:
        """
        保存 K 线。

        如果 K 线已经存在，则更新。
        """

        if not klines:
            return

        rows = [
            (
                kline.symbol,
                kline.interval.value,
                kline.timestamp.isoformat(),
                kline.open,
                kline.high,
                kline.low,
                kline.close,
                kline.volume,
                kline.amount,
            )
            for kline in klines
        ]

        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO kline (
                    symbol,
                    interval,
                    timestamp,
                    open,
                    high,
                    low,
                    close,
                    volume,
                    amount
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT (
                    symbol,
                    interval,
                    timestamp
                )
                DO UPDATE SET
                    open = excluded.open,
                    high = excluded.high,
                    low = excluded.low,
                    close = excluded.close,
                    volume = excluded.volume,
                    amount = excluded.amount
                """,
                rows,
            )

    def save_many(
        self,
        klines_map: dict[str, list[Kline]],
    ) -> None:
        """
        批量保存 K 线。
        """

        for klines in klines_map.values():
            self.save(klines)

    def delete(
        self,
        symbol: str | None = None,
        interval: Interval | None = None,
    ) -> None:
        """
        删除缓存。
        """

        sql = "DELETE FROM kline"

        conditions: list[str] = []
        parameters: list[object] = []

        if symbol is not None:
            conditions.append("symbol = ?")
            parameters.append(symbol)

        if interval is not None:
            conditions.append("interval = ?")
            parameters.append(interval.value)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        with self._connect() as connection:
            connection.execute(
                sql,
                parameters,
            )

    def _initialize(self) -> None:
        """
        初始化数据库。
        """

        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS kline (
                    symbol TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    timestamp TEXT NOT NULL,

                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,

                    volume REAL,
                    amount REAL,

                    PRIMARY KEY (
                        symbol,
                        interval,
                        timestamp
                    )
                )
                """)

            connection.execute("""
                CREATE INDEX IF NOT EXISTS
                idx_kline_symbol_interval_timestamp
                ON kline (
                    symbol,
                    interval,
                    timestamp
                )
                """)

    def _connect(self) -> sqlite3.Connection:
        """
        创建数据库连接。
        """

        connection = sqlite3.connect(self.db_path)

        connection.row_factory = sqlite3.Row

        return connection

    @staticmethod
    def _row_to_kline(
        row: sqlite3.Row,
    ) -> Kline:
        """
        数据库记录转换为 Kline。
        """

        return Kline(
            symbol=row["symbol"],
            interval=Interval(row["interval"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=(float(row["volume"]) if row["volume"] is not None else None),
            amount=(float(row["amount"]) if row["amount"] is not None else None),
        )
