/* =========================================================
   STOCK LAB
   股票详情页
========================================================= */


let currentSymbol = null;

/* =========================================================
   页面初始化
========================================================= */

document.addEventListener("DOMContentLoaded", () => {
    currentSymbol = getStockSymbol();

    if (!currentSymbol) {

        showPageError("没有指定股票代码");

        return;
    }

    // 设置 K 线详情页链接
    updateKlineDetailLink();


    // 先显示当前股票代码
    setText("stockSymbol", currentSymbol);


    // 页面基础功能
    bindResearchTabs();
    bindPeriodButtons();


    // 独立加载
    loadStock();
    loadIndustryCategory();
    loadQuote();
    loadKline();
    loadFinancial();
    loadValuation();
    loadIndustry();
    loadTechnical();
    loadNews();
    loadAnnouncement();
    loadAI();

});



/* =========================================================
   获取当前股票代码
========================================================= */

function getStockSymbol() {

    const params = new URLSearchParams(
        window.location.search
    );

    let symbol = params.get("symbol");

    if (!symbol) {
        return null;
    }

    return symbol.trim().toUpperCase();

}



/* =========================================================
   API 请求
========================================================= */

async function requestAPI(path) {

    const response = await fetch(path);

    if (!response.ok) {

        throw new Error(
            `HTTP ${response.status}`
        );

    }

    const result = await response.json();

    return result;

}



/* =========================================================
   行情
========================================================= */

async function loadStock() {
    try {
        const result = await requestAPI(
            `/api/stock/${encodeURIComponent(currentSymbol)}`
        );

        if (!result || result.success === false) {
            throw new Error(
                result?.message || "股票数据不可用"
            );
        }
        console.log("股票数据:", result);
        const stock = result.data ?? result;

        setText(
            "stockName",
            stock.name
        );

        setText(
            "stockSymbol",
            stock.symbol || currentSymbol
        );

        setText(
            "stockMarket",
            stock.market || "A股"
        );

    } catch (error) {

        console.warn(
            "股票加载失败:",
            error
        );

    }
}

async function loadIndustryCategory() {
    try {
        const result = await requestAPI(
            `/api/industry_category/${encodeURIComponent(currentSymbol)}`
        );
        if (!result || result.success === false) {
            throw new Error(
                result?.message || "行业数据不可用"
            );
        }
        console.log("行业数据:", result);
        const industry = result.data ?? result;

        setText(
            "stockIndustry",
            [
                industry.level_1,
                industry.level_2,
                industry.level_3,
                industry.level_4
            ]
                .filter(Boolean)
                .join(" - ") || "未知行业"
        );

    } catch (error) {

        console.warn(
            "行业加载失败:",
            error
        );

    }
}


function updatePrice(price, change, changePercent) {

    const currentPrice =
        document.getElementById("currentPrice");

    const priceChange =
        document.getElementById("priceChange");

    const priceChangePercent =
        document.getElementById("priceChangePercent");

    const priceChangeBlock =
        document.querySelector(".price-change");


    // =========================================================
    // 最新价
    // =========================================================

    if (
        price !== null &&
        price !== undefined &&
        Number.isFinite(Number(price))
    ) {

        currentPrice.textContent =
            Number(price).toFixed(2);

    } else {

        currentPrice.textContent = "—";

    }


    // =========================================================
    // 涨跌额
    // =========================================================

    if (
        change !== null &&
        change !== undefined &&
        Number.isFinite(Number(change))
    ) {

        const changeValue = Number(change);

        priceChange.textContent =
            changeValue > 0
                ? `+${changeValue.toFixed(2)}`
                : changeValue.toFixed(2);

    } else {

        priceChange.textContent = "—";

    }


    // =========================================================
    // 涨跌幅
    // =========================================================

    if (
        changePercent !== null &&
        changePercent !== undefined &&
        Number.isFinite(Number(changePercent))
    ) {

        const percentValue = Number(changePercent);

        priceChangePercent.textContent =
            percentValue > 0
                ? `+${percentValue.toFixed(2)}%`
                : `${percentValue.toFixed(2)}%`;

    } else {

        priceChangePercent.textContent = "—";

    }


    // =========================================================
    // 涨跌状态
    // =========================================================

    const changeValue = Number(change);

    const elements = [
        currentPrice,
        priceChangeBlock
    ];

    elements.forEach(element => {

        if (!element) {
            return;
        }

        element.classList.remove(
            "positive",
            "negative",
            "flat"
        );

    });


    if (!Number.isFinite(changeValue)) {

        elements.forEach(element => {

            if (element) {
                element.classList.add("flat");
            }

        });

    } else if (changeValue > 0) {

        elements.forEach(element => {

            if (element) {
                element.classList.add("positive");
            }

        });

    } else if (changeValue < 0) {

        elements.forEach(element => {

            if (element) {
                element.classList.add("negative");
            }

        });

    } else {

        elements.forEach(element => {

            if (element) {
                element.classList.add("flat");
            }

        });

    }

}

async function loadQuote() {
    try {
        const result = await requestAPI(
            `/api/quote/${encodeURIComponent(currentSymbol)}`
        );

        if (!result || result.success === false) {
            throw new Error(
                result?.message || "行情数据不可用"
            );
        }

        console.log("行情数据:", result);

        const quote = result.data ?? result;

        // ============================================================
        // 顶部行情
        // ============================================================

        updatePrice(
            quote.last_price,
            quote.change,
            quote.change_percent
        );

        setText(
            "quoteOpen",
            formatNumber(quote.open_price)
        );

        setText(
            "quoteHigh",
            formatNumber(quote.high_price)
        );

        setText(
            "quoteLow",
            formatNumber(quote.low_price)
        );

        setText(
            "quotePrevClose",
            formatNumber(quote.previous_close)
        );

        setText(
            "quoteAmount",
            formatAmount(quote.amount)
        );

        setText(
            "turnover",
            formatPercent(quote.turnover, false)
        );

        setText(
            "marketCap",
            formatAmount(quote.market_cap)
        );

        setText(
            "floatMarketCap",
            formatAmount(quote.float_market_cap)
        );


        // ============================================================
        // 详情页行情
        // ============================================================

        setText(
            "detailPrice",
            formatNumber(quote.last_price)
        );

        setText(
            "detailChange",
            formatSignedNumber(quote.change)
        );

        setText(
            "detailChangePercent",
            formatPercent(quote.change_percent)
        );

        setText(
            "detailVolume",
            formatVolume(quote.volume)
        );

        setText(
            "detailAmount",
            formatAmount(quote.amount)
        );

        setText(
            "detailTurnover",
            formatPercent(quote.turnover)
        );

        setText(
            "detailVolumeRatio",
            formatNumber(quote.volume_ratio)
        )

        setText(
            "detailAmplitude",
            formatPercent(quote.amplitude)
        )


        // ============================================================
        // 数据时间
        // ============================================================

        if (quote.timestamp) {

            setText(
                "dataTime",
                `数据：${quote.timestamp}`
            );

        } else {

            setText(
                "dataTime",
                "数据：实时"
            );

        }


        // ============================================================
        // 行情状态
        // ============================================================

        setText(
            "stockStatus",
            "行情正常"
        );


        // ============================================================
        // 52 周区间
        // ============================================================

        if (
            quote.year_low !== undefined ||
            quote.year_high !== undefined
        ) {

            updateYearRange(
                quote.year_low,
                quote.year_high,
                quote.last_price
            );

        }

    } catch (error) {

        console.warn(
            "行情加载失败:",
            error
        );

        setText(
            "stockStatus",
            "行情暂不可用"
        );

    }
}



/* =========================================================
   K线
========================================================= */

async function loadKline(
    interval = "1d"
) {

    const chart =
        document.getElementById(
            "chartContainer"
        );

    try {

        chart.innerHTML =
            `<div class="data-loading">
                正在加载K线数据...
             </div>`;

        const result = await requestAPI(
            `/api/kline/${encodeURIComponent(currentSymbol)}` +
            `?interval=${encodeURIComponent(interval)}` +
            `&limit=120`
        );

        if (!result || result.success === false) {

            throw new Error(
                result?.message || "K线数据不可用"
            );

        }

        const data =
            result.data ?? [];

        if (!data.length) {

            throw new Error(
                "暂无K线数据"
            );

        }

        renderKline(data);

    }
    catch (error) {

        console.warn(
            "K线加载失败:",
            error
        );

        chart.innerHTML =
            `<div class="empty-state">
                暂无K线数据
             </div>`;

    }

}



/* =========================================================
   K线显示
========================================================= */

function renderKline(data) {

    const chartContainer =
        document.getElementById(
            "chartContainer"
        );

    if (
        !Array.isArray(data) ||
        data.length === 0
    ) {

        chartContainer.innerHTML =
            `<div class="empty-state">
                暂无K线数据
             </div>`;

        return;
    }


    /*
     * 创建图表容器
     */

    chartContainer.innerHTML =
        `<div
            id="klineChart"
            style="
                width: 100%;
                height: 500px;
            "
        ></div>`;


    const chart =
        echarts.init(
            document.getElementById(
                "klineChart"
            )
        );


    /*
     * 按时间排序
     */

    const sortedData =
        [...data].sort(
            (a, b) =>
                new Date(a.timestamp) -
                new Date(b.timestamp)
        );


    /*
     * X轴时间
     */

    const dates =
        sortedData.map(
            item =>
                formatKlineTime(
                    item.timestamp
                )
        );


    /*
     * K线数据
     *
     * ECharts 顺序：
     *
     * [open, close, low, high]
     */

    const candles =
        sortedData.map(
            item => [
                Number(item.open),
                Number(item.close),
                Number(item.low),
                Number(item.high)
            ]
        );


    /*
     * 成交量
     */

    const volumes =
        sortedData.map(
            item =>
                Number(item.volume) || 0
        );


    /*
     * 成交量颜色
     */

    const volumeData =
        sortedData.map(
            item => {

                const open =
                    Number(item.open);

                const close =
                    Number(item.close);

                return {
                    value:
                        Number(item.volume) || 0,

                    itemStyle: {
                        color:
                            close >= open
                                ? "#ef4444"
                                : "#22c55e"
                    }
                };

            }
        );


    /*
     * 配置
     */

    const option = {

        animation: false,

        tooltip: {

            trigger: "axis",

            axisPointer: {
                type: "cross"
            },

            formatter: function (params) {

                const index =
                    params[0].dataIndex;

                const item =
                    sortedData[index];

                if (!item) {
                    return "";
                }

                return `
                    <div>
                        <strong>
                            ${formatKlineTooltipTime(
                    item.timestamp
                )}
                        </strong>

                        <div>
                            开盘：
                            ${formatNumber(item.open)}
                        </div>

                        <div>
                            最高：
                            ${formatNumber(item.high)}
                        </div>

                        <div>
                            最低：
                            ${formatNumber(item.low)}
                        </div>

                        <div>
                            收盘：
                            ${formatNumber(item.close)}
                        </div>

                        <div>
                            成交量：
                            ${formatVolume(item.volume)}
                        </div>

                        <div>
                            成交额：
                            ${formatAmount(item.amount)}
                        </div>
                    </div>
                `;
            }
        },


        grid: [
            {
                left: 60,
                right: 20,
                top: 20,
                height: "65%"
            },

            {
                left: 60,
                right: 20,
                top: "76%",
                height: "16%"
            }
        ],


        xAxis: [

            {
                type: "category",

                data: dates,

                boundaryGap: true,

                axisLine: {
                    lineStyle: {
                        color: "#d1d5db"
                    }
                },

                axisLabel: {
                    color: "#6b7280",
                    hideOverlap: true
                }
            },

            {
                type: "category",

                gridIndex: 1,

                data: dates,

                boundaryGap: true,

                axisLabel: {
                    show: false
                },

                axisLine: {
                    show: false
                }
            }
        ],


        yAxis: [

            {
                scale: true,

                splitArea: {
                    show: false
                },

                axisLabel: {
                    color: "#6b7280"
                },

                splitLine: {
                    lineStyle: {
                        color: "#f0f0f0"
                    }
                }
            },

            {
                scale: true,

                gridIndex: 1,

                axisLabel: {
                    color: "#9ca3af"
                },

                splitLine: {
                    show: false
                }
            }
        ],


        dataZoom: [

            {
                type: "inside",

                xAxisIndex: [
                    0,
                    1
                ],

                start:
                    sortedData.length > 60
                        ? 50
                        : 0,

                end: 100
            },

            {
                type: "slider",

                xAxisIndex: [
                    0,
                    1
                ],

                bottom: 5,

                height: 18,

                start:
                    sortedData.length > 60
                        ? 50
                        : 0,

                end: 100
            }
        ],


        series: [

            {
                name: "K线",

                type: "candlestick",

                data: candles,

                itemStyle: {

                    color: "#ef4444",

                    color0: "#22c55e",

                    borderColor: "#ef4444",

                    borderColor0: "#22c55e"
                }
            },

            {
                name: "成交量",

                type: "bar",

                xAxisIndex: 1,

                yAxisIndex: 1,

                data: volumeData
            }

        ]

    };


    chart.setOption(
        option
    );


    /*
     * 自适应
     */

    window.addEventListener(
        "resize",
        () => {
            chart.resize();
        }
    );


    /*
     * 更新最新指标
     */

    const latest =
        sortedData[
        sortedData.length - 1
        ];

    if (latest) {

        setText(
            "ma5",
            "-"
        );

        setText(
            "ma20",
            "-"
        );

        setText(
            "ma60",
            "-"
        );

        setText(
            "rsi",
            "-"
        );

    }

}

function formatKlineTime(timestamp) {

    if (!timestamp) {
        return "";
    }

    const date =
        new Date(timestamp);

    if (Number.isNaN(date.getTime())) {
        return "";
    }

    const year =
        date.getFullYear();

    const month =
        String(
            date.getMonth() + 1
        ).padStart(2, "0");

    const day =
        String(
            date.getDate()
        ).padStart(2, "0");

    return `${year}-${month}-${day}`;
}


function formatKlineTooltipTime(timestamp) {

    if (!timestamp) {
        return "-";
    }

    const date =
        new Date(timestamp);

    if (Number.isNaN(date.getTime())) {
        return "-";
    }

    const year =
        date.getFullYear();

    const month =
        String(
            date.getMonth() + 1
        ).padStart(2, "0");

    const day =
        String(
            date.getDate()
        ).padStart(2, "0");

    const hour =
        String(
            date.getHours()
        ).padStart(2, "0");

    const minute =
        String(
            date.getMinutes()
        ).padStart(2, "0");

    return (
        `${year}-${month}-${day} ` +
        `${hour}:${minute}`
    );
}


function formatVolume(value) {

    const number =
        Number(value);

    if (!Number.isFinite(number)) {
        return "-";
    }

    if (number >= 100000000) {
        return (
            (number / 100000000)
                .toFixed(2) +
            "亿"
        );
    }

    if (number >= 10000) {
        return (
            (number / 10000)
                .toFixed(2) +
            "万"
        );
    }

    return number.toLocaleString();
}


function formatAmount(value) {

    const number =
        Number(value);

    if (!Number.isFinite(number)) {
        return "-";
    }

    if (number >= 100000000) {
        return (
            (number / 100000000)
                .toFixed(2) +
            "亿"
        );
    }

    if (number >= 10000) {
        return (
            (number / 10000)
                .toFixed(2) +
            "万"
        );
    }

    return number.toLocaleString();
}



/* =========================================================
   财务
========================================================= */

async function loadFinancial() {

    try {

        const result = await requestAPI(
            `/api/financial/${encodeURIComponent(currentSymbol)}`
        );


        if (!result || result.success === false) {

            throw new Error(
                result?.message || "财务数据不可用"
            );

        }


        const data =
            result.data ??
            result;


        renderFinancial(data);

    }
    catch (error) {

        console.warn(
            "财务加载失败:",
            error
        );

    }

}



/* =========================================================
   财务显示
========================================================= */

function renderFinancial(data) {

    if (!data) {
        return;
    }


    setText(
        "financialRevenue",
        formatAmount(data.revenue)
    );


    setText(
        "financialRevenueGrowth",
        formatPercent(data.revenue_growth)
    );


    setText(
        "financialProfit",
        formatAmount(data.net_profit)
    );


    setText(
        "financialProfitGrowth",
        formatPercent(data.net_profit_growth)
    );


    setText(
        "operatingCashFlow",
        formatAmount(data.operating_cash_flow)
    );


    setText(
        "netAssets",
        formatAmount(data.net_assets)
    );


    setText(
        "roe",
        formatPercent(data.roe)
    );


    setText(
        "grossMargin",
        formatPercent(data.gross_margin)
    );


    setText(
        "netMargin",
        formatPercent(data.net_margin)
    );


    setText(
        "revenueGrowth",
        formatPercent(data.revenue_growth)
    );


    setText(
        "profitGrowth",
        formatPercent(data.net_profit_growth)
    );


    setText(
        "dividendYield",
        formatPercent(data.dividend_yield)
    );


    const rows =
        data.history ||
        data.records ||
        [];


    const tbody =
        document.getElementById(
            "financialTableBody"
        );


    if (!rows.length) {
        return;
    }


    tbody.innerHTML = rows.map(
        row => `

            <tr>

                <td>
                    ${escapeHTML(
            row.period ?? "—"
        )}
                </td>

                <td>
                    ${formatAmount(row.revenue)}
                </td>

                <td>
                    ${formatPercent(
            row.revenue_growth
        )}
                </td>

                <td>
                    ${formatAmount(
            row.net_profit
        )}
                </td>

                <td>
                    ${formatPercent(
            row.net_profit_growth
        )}
                </td>

                <td>
                    ${formatPercent(
            row.roe
        )}
                </td>

            </tr>

        `
    ).join("");

}



/* =========================================================
   估值
========================================================= */

async function loadValuation() {
    try {
        const result = await requestAPI(
            `/api/valuation/${encodeURIComponent(currentSymbol)}`
        );

        if (!result || result.success === false) {
            throw new Error(
                result?.message || "估值数据不可用"
            );
        }
        console.log("估值数据:", result);

        const data =
            result.data ??
            result;

        renderValuation(data);

    }
    catch (error) {

        console.warn(
            "估值加载失败:",
            error
        );

    }

}



/* =========================================================
   估值显示
========================================================= */

function renderValuation(data) {

    if (!data) {
        return;
    }


    // ============================================================
    // 核心估值指标
    // ============================================================

    setText(
        "peTtm",
        formatNumber(data.pe_ttm)
    );

    setText(
        "summaryPE",
        formatMultiple(data.pe_ttm)
    );

    setText(
        "summaryPB",
        formatMultiple(data.pb)
    );

    setText(
        "summaryPEG",
        formatNumber(data.peg)
    );


    // ============================================================
    // 估值详情
    // ============================================================

    setText(
        "valuationPE",
        formatMultiple(data.pe_ttm)
    );

    setText(
        "valuationPB",
        formatMultiple(data.pb)
    );

    setText(
        "valuationPS",
        formatMultiple(data.ps_ttm)
    );

    setText(
        "valuationDividend",
        formatPercent(data.dividend_yield)
    );


    // ============================================================
    // 估值说明
    // ============================================================

    setText(
        "valuationPEDesc",
        data.pe_description || "—"
    );

    setText(
        "valuationPBDesc",
        data.pb_description || "—"
    );

    setText(
        "valuationPSDesc",
        data.ps_description || "—"
    );


    setText(
        "summaryPEDesc",
        data.pe_description || "—"
    );

    setText(
        "summaryPBDesc",
        data.pb_description || "—"
    );

    setText(
        "summaryPEGDesc",
        data.peg_description || "—"
    );


    // ============================================================
    // 历史估值区间
    // ============================================================

    setText(
        "valuationLow",
        formatMultiple(data.historical_low)
    );

    setText(
        "valuationCurrent",
        formatMultiple(data.pe_ttm)
    );

    setText(
        "valuationMedian",
        formatMultiple(data.historical_median)
    );

    setText(
        "valuationHigh",
        formatMultiple(data.historical_high)
    );


    // ============================================================
    // 估值说明
    // ============================================================

    setText(
        "valuationNote",
        data.description || "暂无估值分析。"
    );
}


/* =========================================================
   行业
========================================================= */

async function loadIndustry() {

    try {

        const result = await requestAPI(
            `/api/industry/${encodeURIComponent(currentSymbol)}`
        );


        if (!result || result.success === false) {

            throw new Error(
                result?.message || "行业数据不可用"
            );

        }


        const data =
            result.data ??
            result;


        renderIndustry(data);

    }
    catch (error) {

        console.warn(
            "行业加载失败:",
            error
        );

    }

}



/* =========================================================
   行业显示
========================================================= */

function renderIndustry(data) {

    if (!data) {
        return;
    }


    setText(
        "industryName",
        data.name
    );


    setText(
        "detailIndustry",
        data.name
    );


    setText(
        "industryPath",
        data.path
    );


    setText(
        "industryRank",
        data.rank
    );


    setText(
        "industryPosition",
        data.position
    );


    setText(
        "industryProfitability",
        data.profitability
    );


    setText(
        "industryMoat",
        data.moat
    );


    setText(
        "industryDescription",
        data.description
    );


    setText(
        "rankRevenue",
        formatRank(data.rank_revenue)
    );

    setText(
        "rankProfit",
        formatRank(data.rank_profit)
    );

    setText(
        "rankROE",
        formatRank(data.rank_roe)
    );

    setText(
        "rankOverall",
        formatRank(data.rank_overall)
    );


    const competitors =
        data.competitors || [];


    const container =
        document.getElementById(
            "competitorGrid"
        );


    if (!competitors.length) {

        container.innerHTML =
            `<div>
                <strong>—</strong>
                <span>暂无竞争对手数据</span>
             </div>`;

        return;
    }


    container.innerHTML =
        competitors.map(
            item => `

                <div>

                    <strong>
                        ${escapeHTML(
                item.name ?? "—"
            )}
                    </strong>

                    <span>
                        ${escapeHTML(
                item.symbol ?? "—"
            )}
                    </span>

                </div>

            `
        ).join("");

}



/* =========================================================
   技术指标
========================================================= */

async function loadTechnical() {

    try {

        const result = await requestAPI(
            `/api/technical/${encodeURIComponent(currentSymbol)}`
        );


        if (!result || result.success === false) {

            throw new Error(
                result?.message || "技术指标不可用"
            );

        }


        const data =
            result.data ??
            result;


        renderTechnical(data);

    }
    catch (error) {

        console.warn(
            "技术指标加载失败:",
            error
        );

    }

}



/* =========================================================
   技术指标显示
========================================================= */

function renderTechnical(data) {

    if (!data) {
        return;
    }


    setText(
        "technicalMA5",
        formatNumber(data.ma5)
    );

    setText(
        "technicalMA5Status",
        data.ma5_status || "—"
    );


    setText(
        "technicalMA20",
        formatNumber(data.ma20)
    );

    setText(
        "technicalMA20Status",
        data.ma20_status || "—"
    );


    setText(
        "technicalRSI",
        formatNumber(data.rsi)
    );

    setText(
        "technicalRSIStatus",
        data.rsi_status || "—"
    );


    setText(
        "technicalMACD",
        formatNumber(data.macd)
    );

    setText(
        "technicalMACDStatus",
        data.macd_status || "—"
    );


    setText(
        "technicalKDJ",
        formatNumber(data.kdj)
    );

    setText(
        "technicalKDJStatus",
        data.kdj_status || "—"
    );


    setText(
        "technicalATR",
        formatNumber(data.atr)
    );

    setText(
        "technicalATRStatus",
        data.atr_status || "—"
    );


    // 总览技术指标
    setText(
        "ma5",
        formatNumber(data.ma5)
    );

    setText(
        "ma20",
        formatNumber(data.ma20)
    );

    setText(
        "ma60",
        formatNumber(data.ma60)
    );

    setText(
        "rsi",
        formatNumber(data.rsi)
    );

}



/* =========================================================
   资讯
========================================================= */

async function loadNews() {

    try {

        const result = await requestAPI(
            `/api/news/${encodeURIComponent(currentSymbol)}`
        );


        if (!result || result.success === false) {

            throw new Error(
                result?.message || "资讯不可用"
            );

        }


        const data =
            result.data ??
            result;


        renderNews(data);

    }
    catch (error) {

        console.warn(
            "资讯加载失败:",
            error
        );

    }

}



/* =========================================================
   资讯显示
========================================================= */

function renderNews(data) {

    const container =
        document.getElementById(
            "newsList"
        );


    if (!Array.isArray(data) || !data.length) {

        container.innerHTML =
            `<div class="empty-state">
                暂无资讯数据
             </div>`;

        return;
    }


    container.innerHTML =
        data.map(
            item => `

                <article>

                    <span>
                        ${escapeHTML(
                item.category ?? "资讯"
            )}
                    </span>

                    <div>

                        <h3>
                            ${escapeHTML(
                item.title ?? "—"
            )}
                        </h3>

                        <p>
                            ${escapeHTML(
                item.summary ?? ""
            )}
                        </p>

                    </div>

                    <time>
                        ${escapeHTML(
                item.date ?? "—"
            )}
                    </time>

                </article>

            `
        ).join("");

}



/* =========================================================
   公告
========================================================= */

async function loadAnnouncement() {

    try {

        const result = await requestAPI(
            `/api/announcement/${encodeURIComponent(currentSymbol)}`
        );


        if (!result || result.success === false) {

            throw new Error(
                result?.message || "公告不可用"
            );

        }


        const data =
            result.data ??
            result;


        renderAnnouncement(data);

    }
    catch (error) {

        console.warn(
            "公告加载失败:",
            error
        );

    }

}



/* =========================================================
   公告显示
========================================================= */

function renderAnnouncement(data) {

    const container =
        document.getElementById(
            "announcementList"
        );


    if (!Array.isArray(data) || !data.length) {

        container.innerHTML =
            `<div class="empty-state">
                暂无公告数据
             </div>`;

        return;
    }


    container.innerHTML =
        data.map(
            item => `

                <div>

                    <span>
                        ${escapeHTML(
                item.date ?? "—"
            )}
                    </span>

                    <strong>
                        ${escapeHTML(
                item.title ?? "—"
            )}
                    </strong>

                    ${item.url
                    ?
                    `<button
                            onclick="window.open('${escapeAttribute(item.url)}', '_blank')">
                            查看
                         </button>`
                    :
                    `<button disabled>
                            暂无
                         </button>`
                }

                </div>

            `
        ).join("");

}



/* =========================================================
   AI研究
========================================================= */

async function loadAI() {

    try {

        const result = await requestAPI(
            `/api/ai/${encodeURIComponent(currentSymbol)}`
        );


        if (!result || result.success === false) {

            throw new Error(
                result?.message || "AI研究不可用"
            );

        }


        const data =
            result.data ??
            result;


        renderAI(data);

    }
    catch (error) {

        console.warn(
            "AI研究加载失败:",
            error
        );

    }

}



/* =========================================================
   AI显示
========================================================= */

function renderAI(data) {

    if (!data) {
        return;
    }


    setText(
        "aiConclusion",
        data.conclusion
    );


    setText(
        "aiSummary",
        data.summary
    );


    setText(
        "aiFundamental",
        data.fundamental
    );

    setText(
        "aiFundamentalDesc",
        data.fundamental_description
    );


    setText(
        "aiGrowth",
        data.growth
    );

    setText(
        "aiGrowthDesc",
        data.growth_description
    );


    setText(
        "aiValuation",
        data.valuation
    );

    setText(
        "aiValuationDesc",
        data.valuation_description
    );


    setText(
        "aiTechnical",
        data.technical
    );

    setText(
        "aiTechnicalDesc",
        data.technical_description
    );


    setText(
        "aiFundamentalAnalysis",
        data.fundamental_analysis
    );


    setText(
        "aiValuationAnalysis",
        data.valuation_analysis
    );


    setText(
        "aiTechnicalAnalysis",
        data.technical_analysis
    );


    const riskList =
        document.getElementById(
            "aiRiskList"
        );


    const risks =
        data.risks || [];


    if (!risks.length) {

        riskList.innerHTML =
            "<li>暂无风险数据</li>";

        return;
    }


    riskList.innerHTML =
        risks.map(
            risk =>
                `<li>
                    ${escapeHTML(risk)}
                 </li>`
        ).join("");

}



/* =========================================================
   研究评分
========================================================= */

function updateScore(data) {

    if (!data) {
        return;
    }


    setText(
        "overallScore",
        data.overall
    );


    setText(
        "scoreLabel",
        data.label
    );


    setText(
        "scoreDescription",
        data.description
    );


    updateScoreBar(
        "fundamentalScore",
        "fundamentalScoreBar",
        data.fundamental
    );


    updateScoreBar(
        "growthScore",
        "growthScoreBar",
        data.growth
    );


    updateScoreBar(
        "valuationScore",
        "valuationScoreBar",
        data.valuation
    );


    updateScoreBar(
        "technicalScore",
        "technicalScoreBar",
        data.technical
    );

}



function updateScoreBar(
    textId,
    barId,
    value
) {

    if (
        value === undefined ||
        value === null
    ) {

        setText(
            textId,
            "—"
        );

        return;
    }


    setText(
        textId,
        value
    );


    const bar =
        document.getElementById(barId);


    if (bar) {

        bar.style.width =
            `${Math.max(
                0,
                Math.min(100, Number(value))
            )}%`;

    }

}



/* =========================================================
   研究 Tab
========================================================= */

function bindResearchTabs() {

    const tabs =
        document.querySelectorAll(
            "#researchTabs button"
        );


    tabs.forEach(button => {

        button.addEventListener(
            "click",
            () => {

                const target =
                    button.dataset.target;

                switchSection(target);

            }
        );

    });

}



function switchSection(target) {

    document
        .querySelectorAll(
            ".research-tabs button"
        )
        .forEach(button => {

            button.classList.toggle(
                "active",
                button.dataset.target === target
            );

        });


    document
        .querySelectorAll(
            ".research-section"
        )
        .forEach(section => {

            section.classList.toggle(
                "active",
                section.id === target
            );

        });

}



/* =========================================================
   K线周期
========================================================= */

function bindPeriodButtons() {

    document
        .querySelectorAll(
            ".period-buttons button"
        )
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    document
                        .querySelectorAll(
                            ".period-buttons button"
                        )
                        .forEach(item => {

                            item.classList.remove(
                                "active"
                            );

                        });


                    button.classList.add(
                        "active"
                    );


                    const period =
                        button.dataset.period;


                    loadKline(period);

                }
            );

        });

}



/* =========================================================
   52周区间
========================================================= */

function updateYearRange(
    low,
    high,
    current
) {

    if (
        low === undefined ||
        high === undefined ||
        current === undefined
    ) {
        return;
    }


    setText(
        "yearLow",
        formatNumber(low)
    );


    setText(
        "yearHigh",
        formatNumber(high)
    );


    setText(
        "yearCurrent",
        `当前 ${formatNumber(current)}`
    );


    const range =
        Number(high) - Number(low);


    if (range <= 0) {
        return;
    }


    const percentage =
        (
            (Number(current) - Number(low))
            / range
        ) * 100;


    const progress =
        document.getElementById(
            "yearRangeProgress"
        );


    if (progress) {

        progress.style.width =
            `${Math.max(
                0,
                Math.min(100, percentage)
            )}%`;

    }


    setText(
        "yearRangeDescription",
        `当前价格位于52周区间约 ${percentage.toFixed(1)}%`
    );

}



/* =========================================================
   工具函数
========================================================= */

function setText(
    id,
    value
) {

    const element =
        document.getElementById(id);


    if (!element) {
        return;
    }


    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {

        element.textContent = "—";

        return;
    }


    element.textContent =
        String(value);

}



function formatNumber(value) {

    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {
        return "—";
    }


    const number =
        Number(value);


    if (Number.isNaN(number)) {
        return "—";
    }


    return number.toLocaleString(
        "zh-CN",
        {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }
    );

}



function formatSignedNumber(value) {

    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {
        return "—";
    }


    const number =
        Number(value);


    if (Number.isNaN(number)) {
        return "—";
    }


    const prefix =
        number > 0
            ? "+"
            : "";


    return prefix +
        number.toLocaleString(
            "zh-CN",
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        );

}



function formatPercent(value, showPlus = true) {

    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {
        return "—";
    }

    const number = Number(value);

    if (Number.isNaN(number)) {
        return "—";
    }

    if (number > 0) {

        return (
            (showPlus ? "+" : "") +
            number.toFixed(2) +
            "%"
        );

    }

    if (number < 0) {

        return (
            number.toFixed(2) +
            "%"
        );

    }

    return "0%";
}



function formatMultiple(value) {

    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {
        return "—";
    }


    const number =
        Number(value);


    if (Number.isNaN(number)) {
        return "—";
    }


    return number.toFixed(2) + "x";

}



function formatAmount(value) {

    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {
        return "—";
    }


    const number =
        Number(value);


    if (Number.isNaN(number)) {
        return "—";
    }


    const abs =
        Math.abs(number);


    if (abs >= 1000000000000) {
        return (
            number / 1000000000000
        ).toFixed(2) + "万亿";
    }

    if (abs >= 100000000) {
        return (
            number / 100000000
        ).toFixed(2) + "亿";
    }

    if (abs >= 10000) {
        return (
            number / 10000
        ).toFixed(2) + "万";

    }


    return number.toLocaleString(
        "zh-CN",
        {
            maximumFractionDigits: 2
        }
    );

}



function formatVolume(value) {

    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {
        return "—";
    }


    const number =
        Number(value);


    if (Number.isNaN(number)) {
        return "—";
    }


    if (number >= 10000) {

        return (
            number / 10000
        ).toFixed(2) + "万";

    }


    return number.toLocaleString(
        "zh-CN"
    );

}



function formatRank(value) {

    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {
        return "—";
    }


    return "#" + value;

}



function applyChangeClass(
    elementId,
    value
) {

    const element =
        document.getElementById(
            elementId
        );


    if (!element) {
        return;
    }


    element.classList.remove(
        "positive",
        "negative"
    );


    const number =
        Number(value);


    if (number > 0) {

        element.classList.add(
            "positive"
        );

    }
    else if (number < 0) {

        element.classList.add(
            "negative"
        );

    }

}



function escapeHTML(value) {

    if (
        value === undefined ||
        value === null
    ) {
        return "";
    }


    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}



function escapeAttribute(value) {

    return escapeHTML(value);

}



/* =========================================================
   页面错误
========================================================= */

function showPageError(message) {

    const page =
        document.querySelector(
            ".stock-detail-page"
        );


    if (!page) {
        return;
    }


    page.innerHTML =
        `
        <div class="panel"
             style="
                margin-top:40px;
                padding:60px;
                text-align:center;
             ">

            <h2>
                股票详情无法加载
            </h2>

            <p>
                ${escapeHTML(message)}
            </p>

            <button
                class="primary-button"
                onclick="goBackStock()">

                返回股票列表

            </button>

        </div>
        `;

}



/* =========================================================
   页面导航
========================================================= */

function goBackStock() {

    window.history.back();

}



function goHome() {

    window.location.href =
        "../";

}



/* =========================================================
   自选
========================================================= */

function toggleFavorite() {

    const button =
        document.getElementById(
            "favoriteButton"
        );


    if (!button) {
        return;
    }


    const active =
        button.classList.toggle(
            "active"
        );


    button.textContent =
        active
            ? "★ 已自选"
            : "☆ 自选";

}



/* =========================================================
   AI
========================================================= */

function scrollToAI() {

    switchSection("ai");


    const element =
        document.getElementById("ai");


    if (element) {

        element.scrollIntoView({
            behavior: "smooth"
        });

    }

}

function updateKlineDetailLink() {

    const link =
        document.getElementById(
            "klineDetailLink"
        );

    if (!link || !currentSymbol) {
        return;
    }

    link.href =
        `kline.html?symbol=${encodeURIComponent(
            currentSymbol
        )}`;
}

/* =========================================================
   分时成交量
========================================================= */

/**
 * 格式化成交量。
 *
 * @param {number} value
 * @returns {string}
 */
function formatVolume(value) {

    value = Number(value) || 0;


    if (value >= 100000000) {

        return (
            value / 100000000
        ).toFixed(2) + "亿";

    }


    if (value >= 10000) {

        return (
            value / 10000
        ).toFixed(2) + "万";

    }


    return Math.round(
        value
    ).toLocaleString();

}


/**
 * 渲染分时成交量。
 *
 * 数据格式：
 *
 * [
 *     {
 *         time: "09:31",
 *         volume: 125800
 *     },
 *     {
 *         time: "09:32",
 *         volume: 182600
 *     }
 * ]
 *
 * @param {Array} data
 */
function renderIntradayVolume(data) {

    const container =
        document.getElementById(
            "intradayVolumeBars"
        );


    const totalElement =
        document.getElementById(
            "intradayVolume"
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    /*
     * 没有分时数据。
     */

    if (
        !Array.isArray(data) ||
        data.length === 0
    ) {

        if (totalElement) {

            totalElement.textContent =
                "—";

        }

        return;
    }


    /*
     * 提取成交量。
     */

    const volumes =
        data.map(item =>
            Number(item.volume) || 0
        );


    /*
     * 找到最高成交量。
     */

    const maxVolume =
        Math.max(...volumes);


    /*
     * 计算累计成交量。
     */

    const totalVolume =
        volumes.reduce(
            (sum, value) =>
                sum + value,
            0
        );


    if (totalElement) {

        totalElement.textContent =
            formatVolume(
                totalVolume
            );

    }


    /*
     * 创建成交量柱。
     */

    data.forEach(item => {

        const volume =
            Number(item.volume) || 0;


        const bar =
            document.createElement(
                "i"
            );


        bar.className =
            "volume-bar";


        /*
         * 根据成交量计算柱高。
         *
         * 最低保持 4%，避免极小成交量
         * 完全看不见。
         */

        const height =
            maxVolume > 0
                ? Math.max(
                    4,
                    volume / maxVolume * 100
                )
                : 4;


        bar.style.height =
            `${height}%`;


        /*
         * 鼠标悬停显示时间和成交量。
         */

        const time =
            item.time || "";


        bar.title =
            `${time}  ${formatVolume(volume)}`;


        container.appendChild(
            bar
        );

    });

}


/* =========================================================
   K 线数据 → 分时成交量
========================================================= */

/**
 * 从分钟 K 线数据生成分时成交量。
 *
 * 支持：
 *
 * item.datetime
 * item.time
 *
 * @param {Array} klines
 */
function renderIntradayVolumeFromKlines(
    klines
) {

    if (
        !Array.isArray(klines) ||
        klines.length === 0
    ) {

        renderIntradayVolume([]);

        return;
    }


    const data =
        klines.map(item => {

            const datetime =
                item.datetime ||
                item.time;


            let time = "";


            if (datetime) {

                const date =
                    new Date(datetime);


                if (
                    !Number.isNaN(
                        date.getTime()
                    )
                ) {

                    time =
                        date.toLocaleTimeString(
                            "zh-CN",
                            {
                                hour: "2-digit",
                                minute: "2-digit",
                                hour12: false
                            }
                        );

                }

            }


            return {

                time,

                volume:
                    Number(
                        item.volume
                    ) || 0

            };

        });


    renderIntradayVolume(
        data
    );

}