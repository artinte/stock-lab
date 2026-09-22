from __future__ import annotations

import random

from core.models.industry_performance import (
    IndustryPerformance,
)


class IndustryPerformanceMock:
    """
    行业行情 Mock 数据。

    后续接入 Gateway 后，可以直接替换这个类。
    """

    INDUSTRIES = {
        1: [
            ("CI005", "金融"),
            ("CI001", "能源"),
            ("CI002", "材料"),
            ("CI003", "工业"),
            ("CI004", "可选消费"),
            ("CI006", "医药卫生"),
            ("CI007", "信息技术"),
            ("CI008", "通信"),
            ("CI009", "公用事业"),
        ],
        2: [
            ("CI005001", "银行", "CI005"),
            ("CI005002", "非银行金融", "CI005"),
            ("CI001001", "石油石化", "CI001"),
            ("CI001002", "煤炭", "CI001"),
            ("CI002001", "基础化工", "CI002"),
            ("CI002002", "有色金属", "CI002"),
            ("CI003001", "机械", "CI003"),
            ("CI003002", "电力设备", "CI003"),
            ("CI004001", "食品饮料", "CI004"),
            ("CI004002", "家电", "CI004"),
            ("CI006001", "医药", "CI006"),
            ("CI007001", "计算机", "CI007"),
            ("CI007002", "电子", "CI007"),
            ("CI008001", "通信", "CI008"),
        ],
        3: [
            ("CI005001001", "国有银行", "CI005001"),
            ("CI005001002", "股份制银行", "CI005001"),
            ("CI005002001", "证券", "CI005002"),
            ("CI005002002", "保险", "CI005002"),
            ("CI001001001", "石油开采", "CI001001"),
            ("CI002002001", "工业金属", "CI002002"),
            ("CI003001001", "通用机械", "CI003001"),
            ("CI003002001", "光伏设备", "CI003002"),
            ("CI004001001", "白酒", "CI004001"),
            ("CI007001001", "软件开发", "CI007001"),
            ("CI007002001", "半导体", "CI007002"),
            ("CI008001001", "通信设备", "CI008001"),
        ],
        4: [
            ("CI005001001001", "国有大型银行", "CI005001001"),
            ("CI005001002001", "股份制银行", "CI005001002"),
            ("CI005002001001", "证券公司", "CI005002001"),
            ("CI005002002001", "保险公司", "CI005002002"),
            ("CI003002001001", "光伏电池", "CI003002001"),
            ("CI007001001001", "应用软件", "CI007001001"),
            ("CI007002001001", "半导体材料", "CI007002001"),
            ("CI007002001002", "集成电路", "CI007002001"),
        ],
    }

    def get_daily(
        self,
        date: str,
        level: int = 2,
        method: str = "weighted",
    ) -> list[IndustryPerformance]:

        if level not in self.INDUSTRIES:
            raise ValueError(f"不支持的行业层级: {level}")

        random.seed(f"{date}-{level}-{method}")

        result = []

        for item in self.INDUSTRIES[level]:

            code = item[0]
            name = item[1]
            parent_code = item[2] if len(item) > 2 else None

            stocks = random.randint(20, 120)

            up = random.randint(
                int(stocks * 0.2),
                int(stocks * 0.7),
            )

            down = random.randint(
                int(stocks * 0.1),
                int(stocks * 0.5),
            )

            flat = stocks - up - down

            if flat < 0:
                flat = 0

            pct = round(
                random.uniform(-4.5, 5.5),
                2,
            )

            result.append(
                IndustryPerformance(
                    code=code,
                    name=name,
                    level=level,
                    parent_code=parent_code,
                    pct=pct,
                    stocks=stocks,
                    up=up,
                    down=down,
                    flat=flat,
                    amount=round(
                        random.uniform(5, 800),
                        2,
                    ),
                    market_cap=round(
                        random.uniform(500, 12000),
                        2,
                    ),
                    float_market_cap=round(
                        random.uniform(400, 9000),
                        2,
                    ),
                )
            )

        return result