/* =========================================================
   STOCK LAB - 专业K线
========================================================= */

let chart = null;

let symbol = "";

let currentInterval = "1d";

let currentLimit = 120;

let klineData = [];


/* =========================================================
   Interval 定义
   必须与 Python Interval 保持一致
========================================================= */

const INTERVALS = {

    "1m": {
        name: "1分",
        format: "time",
    },

    "5m": {
        name: "5分",
        format: "time",
    },

    "15m": {
        name: "15分",
        format: "time",
    },

    "30m": {
        name: "30分",
        format: "time",
    },

    "60m": {
        name: "60分",
        format: "time",
    },

    "1d": {
        name: "日K",
        format: "date",
    },

    "1w": {
        name: "周K",
        format: "date",
    },

    "1M": {
        name: "月K",
        format: "date",
    },

};


/* =========================================================
   初始化
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        console.log("初始化专业K线页面");

        initSymbol();

        initChart();

        initEvents();

        initDefaultDate();

        loadKline();

    }
);


/* =========================================================
   获取 URL 中的股票代码
========================================================= */

function initSymbol() {

    const params =
        new URLSearchParams(
            window.location.search
        );

    symbol =
        params.get("symbol")?.trim().toUpperCase() || "";

    document
        .getElementById("symbolInput")
        .value = symbol;

    document
        .getElementById("stockSymbol")
        .textContent =
        symbol || "未指定股票";

}


/* =========================================================
   初始化默认时间范围
========================================================= */

function initDefaultDate() {

    const end = new Date();

    const start = new Date(
        end.getTime()
    );


    switch (currentInterval) {

        case "1m":
        case "5m":
        case "15m":

            // 分钟K：最近5天
            start.setDate(
                start.getDate() - 5
            );

            break;


        case "30m":
        case "60m":

            // 30分钟 / 60分钟：最近1个月
            start.setMonth(
                start.getMonth() - 1
            );

            break;


        case "1d":

            // 日K：最近1年
            start.setFullYear(
                start.getFullYear() - 1
            );

            break;


        case "1w":

            // 周K：最近3年
            start.setFullYear(
                start.getFullYear() - 3
            );

            break;


        case "1M":

            // 月K：最近10年
            start.setFullYear(
                start.getFullYear() - 10
            );

            break;

    }


    document
        .getElementById("startTime")
        .value =
        formatDateTimeLocal(start);


    document
        .getElementById("endTime")
        .value =
        formatDateTimeLocal(end);

}


/* =========================================================
   datetime-local 格式
========================================================= */

function formatDateTimeLocal(
    date
) {

    return (
        date.getFullYear() +
        "-" +
        String(
            date.getMonth() + 1
        ).padStart(2, "0") +
        "-" +
        String(
            date.getDate()
        ).padStart(2, "0") +
        "T" +
        String(
            date.getHours()
        ).padStart(2, "0") +
        ":" +
        String(
            date.getMinutes()
        ).padStart(2, "0")
    );

}


/* =========================================================
   初始化图表
========================================================= */

function initChart() {

    const element =
        document.getElementById("klineChart");

    chart =
        echarts.init(element);

    window.addEventListener(
        "resize",
        () => {

            if (chart) {
                chart.resize();
            }

        }
    );

}


/* =========================================================
   初始化事件
========================================================= */

function initEvents() {

    /* 周期 */

    document
        .querySelectorAll(".period-button")
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    const interval =
                        button.dataset.interval;

                    setIntervalButton(
                        interval
                    );

                    currentInterval =
                        interval;

                    /*
                     * 切换周期后，
                     * 自动设置对应的默认时间范围。
                     */

                    initDefaultDate();

                    loadKline();

                }
            );

        });


    /* 数量 */

    document
        .querySelectorAll(".range-button")
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    const range =
                        Number(
                            button.dataset.range
                        );

                    currentLimit =
                        range;

                    document
                        .querySelectorAll(
                            ".range-button"
                        )
                        .forEach(item => {

                            item.classList.remove(
                                "active"
                            );

                        });

                    button.classList.add(
                        "active"
                    );

                    loadKline();

                }
            );

        });


    /* 搜索 */

    document
        .getElementById("searchButton")
        .addEventListener(
            "click",
            searchSymbol
        );


    document
        .getElementById("symbolInput")
        .addEventListener(
            "keydown",
            event => {

                if (event.key === "Enter") {
                    searchSymbol();
                }

            }
        );


    /* 时间查询 */

    document
        .getElementById("applyDateButton")
        .addEventListener(
            "click",
            () => {

                loadKline();

            }
        );


    /* 清除时间 */

    document
        .getElementById("clearDateButton")
        .addEventListener(
            "click",
            () => {

                document
                    .getElementById("startTime")
                    .value = "";

                document
                    .getElementById("endTime")
                    .value = "";

                loadKline();

            }
        );


    /* 返回股票 */

    document
        .getElementById("backButton")
        .addEventListener(
            "click",
            () => {

                if (!symbol) {

                    window.location.href =
                        "../stock/";

                    return;

                }

                window.location.href =
                    `../stock/stock_detail.html?symbol=${encodeURIComponent(symbol)}`;

            }
        );

}


/* =========================================================
   搜索股票
========================================================= */

function searchSymbol() {

    const input =
        document
            .getElementById("symbolInput")
            .value
            .trim()
            .toUpperCase();

    if (!input) {
        return;
    }

    symbol = input;

    const url =
        new URL(
            window.location.href
        );

    url.searchParams.set(
        "symbol",
        symbol
    );

    window.history.replaceState(
        {},
        "",
        url
    );

    document
        .getElementById("stockSymbol")
        .textContent = symbol;

    /*
     * 搜索新股票时，
     * 使用当前周期对应的默认时间范围。
     */

    initDefaultDate();

    loadKline();

}


/* =========================================================
   加载 K 线
========================================================= */

async function loadKline() {
    if (!symbol) {
        showStatus(
            "未指定股票代码"
        );
        hideLoading();
        return;
    }

    showLoading();

    showStatus(
        `正在加载 ${symbol} ${currentInterval}`
    );


    const params =
        new URLSearchParams();

    params.set("interval", currentInterval);
    params.set("limit", currentLimit);

    const startTime = document
        .getElementById("startTime")
        .value;

    if (startTime) {
        params.set(
            "start_time",
            toISOStringWithoutTimezone(
                startTime
            )
        );

    }

    const endTime =
        document
            .getElementById("endTime")
            .value;

    if (endTime) {
        params.set(
            "end_time",
            toISOStringWithoutTimezone(
                endTime
            )
        );

    }

    const url =
        `/api/kline/${encodeURIComponent(symbol)}` +
        `?${params.toString()}`;

    console.log(
        `📊 请求K线：${url}`
    );


    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        const result =
            await response.json();

        if (!result.success) {
            throw new Error(
                result.message ||
                "K线获取失败"
            );
        }

        const rows = result.data || [];
        if (!rows.length) {
            throw new Error(
                "暂无K线数据"
            );
        }

        klineData =
            normalizeKlineData(rows);


        if (!klineData.length) {

            throw new Error(
                "K线数据格式错误"
            );

        }


        console.log(
            `✅ 获取 ${klineData.length} 根K线`
        );


        updateSummary();

        updateIndicators();

        renderChart();

        updateFooter();

        hideLoading();

        showStatus(
            `已加载 ${klineData.length} 根K线`
        );


    } catch (error) {

        console.error(
            "❌ K线加载失败：",
            error
        );

        klineData = [];

        clearChart();

        hideLoading();

        showStatus(
            error.message ||
            "K线加载失败"
        );

    }

}


/* =========================================================
   K线数据标准化
========================================================= */

function normalizeKlineData(rows) {

    return rows
        .map(item => {

            return {

                timestamp:
                    item.timestamp,

                open:
                    Number(item.open),

                high:
                    Number(item.high),

                low:
                    Number(item.low),

                close:
                    Number(item.close),

                volume:
                    item.volume == null
                        ? null
                        : Number(item.volume),

                amount:
                    item.amount == null
                        ? null
                        : Number(item.amount),

            };

        })
        .filter(item => {

            return (
                item.timestamp &&
                Number.isFinite(item.open) &&
                Number.isFinite(item.high) &&
                Number.isFinite(item.low) &&
                Number.isFinite(item.close)
            );

        })
        .sort(
            (a, b) =>
                new Date(a.timestamp) -
                new Date(b.timestamp)
        );

}


/* =========================================================
   绘制专业 K 线
========================================================= */

function renderChart() {

    const dates =
        klineData.map(
            item =>
                formatChartTime(
                    item.timestamp
                )
        );


    const candles =
        klineData.map(
            item => [

                item.open,

                item.close,

                item.low,

                item.high,

            ]
        );


    const volumes =
        klineData.map(
            item => {

                const value =
                    item.volume ?? 0;

                return {

                    value,

                    itemStyle: {

                        /*
                         * 上涨：
                         * close >= open
                         *
                         * 下跌：
                         * close < open
                         */

                        color:
                            item.close >= item.open
                                ? "#ef4444"
                                : "#22c55e",

                    },

                };

            }
        );


    const ma5 =
        calculateMA(
            klineData,
            5
        );

    const ma10 =
        calculateMA(
            klineData,
            10
        );

    const ma20 =
        calculateMA(
            klineData,
            20
        );

    const ma60 =
        calculateMA(
            klineData,
            60
        );


    const option = {

        animation: false,

        backgroundColor: "#ffffff",


        tooltip: {

            trigger: "axis",

            axisPointer: {

                type: "cross",

                link: [
                    {
                        xAxisIndex: "all",
                    },
                ],

            },

            backgroundColor:
                "rgba(17, 24, 39, 0.94)",

            borderWidth: 0,

            textStyle: {

                color: "#ffffff",

                fontSize: 12,

            },

            formatter: function (
                params
            ) {

                return buildTooltip(
                    params
                );

            },

        },


        axisPointer: {

            link: [
                {
                    xAxisIndex: "all",
                },
            ],

        },


        grid: [

            {
                left: 70,
                right: 75,
                top: 30,
                height: "60%",
            },

            {
                left: 70,
                right: 75,
                top: "72%",
                height: "17%",
            },

        ],


        xAxis: [

            {

                type: "category",

                data: dates,

                boundaryGap: true,

                axisLine: {

                    lineStyle: {

                        color: "#d1d5db",

                    },

                },

                axisLabel: {

                    color: "#6b7280",

                    fontSize: 11,

                },

                splitLine: {

                    show: false,

                },

            },

            {

                type: "category",

                gridIndex: 1,

                data: dates,

                boundaryGap: true,

                axisLine: {

                    lineStyle: {

                        color: "#d1d5db",

                    },

                },

                axisLabel: {

                    color: "#6b7280",

                    fontSize: 11,

                },

            },

        ],


        yAxis: [

            {

                scale: true,

                position: "right",

                splitNumber: 5,

                axisLine: {

                    show: true,

                    lineStyle: {

                        color: "#d1d5db",

                    },

                },

                axisLabel: {

                    color: "#6b7280",

                    fontSize: 11,

                    formatter: value =>
                        formatPrice(value),

                },

                splitLine: {

                    lineStyle: {

                        color: "#f0f1f3",

                    },

                },

            },

            {

                gridIndex: 1,

                position: "right",

                splitNumber: 2,

                axisLine: {

                    show: true,

                    lineStyle: {

                        color: "#d1d5db",

                    },

                },

                axisLabel: {

                    color: "#9ca3af",

                    fontSize: 10,

                    formatter: value =>
                        formatVolume(value),

                },

                splitLine: {

                    lineStyle: {

                        color: "#f3f4f6",

                    },

                },

            },

        ],


        dataZoom: [

            {

                type: "inside",

                xAxisIndex: [
                    0,
                    1,
                ],

                start: 60,

                end: 100,

            },

            {

                type: "slider",

                xAxisIndex: [
                    0,
                    1,
                ],

                bottom: 12,

                height: 18,

                borderColor: "#e5e7eb",

                backgroundColor:
                    "#f9fafb",

                fillerColor:
                    "rgba(107, 114, 128, 0.12)",

                handleStyle: {

                    color: "#6b7280",

                },

            },

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

                    borderColor0: "#22c55e",

                },

            },


            {

                name: "MA5",

                type: "line",

                data: ma5,

                smooth: false,

                showSymbol: false,

                lineStyle: {

                    width: 1,

                },

            },


            {

                name: "MA10",

                type: "line",

                data: ma10,

                smooth: false,

                showSymbol: false,

                lineStyle: {

                    width: 1,

                },

            },


            {

                name: "MA20",

                type: "line",

                data: ma20,

                smooth: false,

                showSymbol: false,

                lineStyle: {

                    width: 1,

                },

            },


            {

                name: "MA60",

                type: "line",

                data: ma60,

                smooth: false,

                showSymbol: false,

                lineStyle: {

                    width: 1,

                },

            },


            {

                name: "成交量",

                type: "bar",

                xAxisIndex: 1,

                yAxisIndex: 1,

                data: volumes,

                barMaxWidth: 8,

            },

        ],

    };


    chart.setOption(
        option,
        true
    );

}


/* =========================================================
   MA
========================================================= */

function calculateMA(
    data,
    period
) {

    const result = [];

    for (
        let i = 0;
        i < data.length;
        i++
    ) {

        if (i < period - 1) {

            result.push(
                "-"
            );

            continue;

        }


        let sum = 0;

        for (
            let j = 0;
            j < period;
            j++
        ) {

            sum +=
                data[
                    i - j
                ].close;

        }


        result.push(
            sum / period
        );

    }

    return result;

}


/* =========================================================
   Tooltip
========================================================= */

function buildTooltip(
    params
) {

    if (!params || !params.length) {
        return "";
    }


    const index =
        params[0].dataIndex;

    const item =
        klineData[index];


    if (!item) {
        return "";
    }


    const date =
        formatFullTime(
            item.timestamp
        );


    const change =
        index > 0
            ? item.close -
            klineData[index - 1].close
            : null;


    const changePercent =
        index > 0 &&
            klineData[index - 1].close
            ? (
                change /
                klineData[index - 1].close
            ) * 100
            : null;


    let html = "";


    html +=
        `<div style="margin-bottom:8px;">` +
        `${date}` +
        `</div>`;


    html +=
        `开盘：${formatPrice(item.open)}<br>`;

    html +=
        `最高：${formatPrice(item.high)}<br>`;

    html +=
        `最低：${formatPrice(item.low)}<br>`;

    html +=
        `收盘：${formatPrice(item.close)}<br>`;


    if (change !== null) {

        html +=
            `涨跌：${formatSigned(change)} ` +
            `(${formatSignedPercent(changePercent)})<br>`;

    }


    html +=
        `成交量：${formatVolume(item.volume)}<br>`;

    html +=
        `成交额：${formatAmount(item.amount)}`;


    return html;

}


/* =========================================================
   顶部行情摘要
========================================================= */

function updateSummary() {

    if (!klineData.length) {
        return;
    }


    const last =
        klineData[
        klineData.length - 1
        ];


    const previous =
        klineData.length > 1
            ? klineData[
            klineData.length - 2
            ]
            : null;


    document
        .getElementById("currentPrice")
        .textContent =
        formatPrice(
            last.close
        );


    document
        .getElementById("quoteOpen")
        .textContent =
        formatPrice(
            last.open
        );


    document
        .getElementById("quoteHigh")
        .textContent =
        formatPrice(
            last.high
        );


    document
        .getElementById("quoteLow")
        .textContent =
        formatPrice(
            last.low
        );


    document
        .getElementById("quoteVolume")
        .textContent =
        formatVolume(
            last.volume
        );


    document
        .getElementById("quoteAmount")
        .textContent =
        formatAmount(
            last.amount
        );


    if (previous) {

        const change =
            last.close -
            previous.close;

        const percent =
            previous.close
                ? (
                    change /
                    previous.close
                ) * 100
                : null;


        document
            .getElementById("priceChange")
            .textContent =
            formatSigned(
                change
            );


        document
            .getElementById(
                "priceChangePercent"
            )
            .textContent =
            formatSignedPercent(
                percent
            );


        const elements = [

            document.getElementById(
                "currentPrice"
            ),

            document.getElementById(
                "priceChange"
            ),

            document.getElementById(
                "priceChangePercent"
            ),

        ];


        elements.forEach(
            element => {

                element.style.color =
                    change >= 0
                        ? "#ef4444"
                        : "#16a34a";

            }
        );

    }


    document
        .getElementById("stockSymbol")
        .textContent =
        symbol;

}


/* =========================================================
   指标摘要
========================================================= */

function updateIndicators() {

    document
        .getElementById("ma5")
        .textContent =
        formatPrice(
            getLastMA(5)
        );


    document
        .getElementById("ma10")
        .textContent =
        formatPrice(
            getLastMA(10)
        );


    document
        .getElementById("ma20")
        .textContent =
        formatPrice(
            getLastMA(20)
        );


    document
        .getElementById("ma60")
        .textContent =
        formatPrice(
            getLastMA(60)
        );

}


function getLastMA(
    period
) {

    if (
        klineData.length <
        period
    ) {

        return null;

    }


    let sum = 0;


    for (
        let i = 0;
        i < period;
        i++
    ) {

        sum +=
            klineData[
                klineData.length -
                1 -
                i
            ].close;

    }


    return sum / period;

}


/* =========================================================
   Footer
========================================================= */

function updateFooter() {

    document
        .getElementById(
            "currentInterval"
        )
        .textContent =
        currentInterval;


    document
        .getElementById(
            "dataCount"
        )
        .textContent =
        klineData.length;


    if (klineData.length) {

        document
            .getElementById(
                "lastTime"
            )
            .textContent =
            formatFullTime(
                klineData[
                    klineData.length - 1
                ].timestamp
            );

    }

}


/* =========================================================
   设置周期按钮
========================================================= */

function setIntervalButton(
    interval
) {

    document
        .querySelectorAll(
            ".period-button"
        )
        .forEach(
            button => {

                button.classList.toggle(
                    "active",
                    button.dataset.interval ===
                    interval
                );

            }
        );

}


/* =========================================================
   时间格式
========================================================= */

function formatChartTime(
    timestamp
) {

    const date =
        new Date(timestamp);


    if (
        currentInterval === "1d" ||
        currentInterval === "1w" ||
        currentInterval === "1M"
    ) {

        return (
            date.getFullYear() +
            "-" +
            String(
                date.getMonth() + 1
            ).padStart(2, "0") +
            "-" +
            String(
                date.getDate()
            ).padStart(2, "0")
        );

    }


    return (
        String(
            date.getMonth() + 1
        ).padStart(2, "0") +
        "-" +
        String(
            date.getDate()
        ).padStart(2, "0") +
        " " +
        String(
            date.getHours()
        ).padStart(2, "0") +
        ":" +
        String(
            date.getMinutes()
        ).padStart(2, "0")
    );

}


function formatFullTime(
    timestamp
) {

    const date =
        new Date(timestamp);

    if (
        currentInterval === "1d" ||
        currentInterval === "1w" ||
        currentInterval === "1M"
    ) {

        return (
            date.getFullYear() +
            "-" +
            String(
                date.getMonth() + 1
            ).padStart(2, "0") +
            "-" +
            String(
                date.getDate()
            ).padStart(2, "0")
        );

    }


    return (
        date.getFullYear() +
        "-" +
        String(
            date.getMonth() + 1
        ).padStart(2, "0") +
        "-" +
        String(
            date.getDate()
        ).padStart(2, "0") +
        " " +
        String(
            date.getHours()
        ).padStart(2, "0") +
        ":" +
        String(
            date.getMinutes()
        ).padStart(2, "0")
    );

}


/* =========================================================
   datetime-local → API 时间
========================================================= */

function toISOStringWithoutTimezone(
    value
) {

    if (!value) {
        return "";
    }

    /*
     * FastAPI datetime 可以直接解析：
     *
     * 2026-09-11T09:30:00
     */

    return value.length === 16
        ? `${value}:00`
        : value;

}


/* =========================================================
   格式化
========================================================= */

function formatPrice(
    value
) {

    if (
        value === null ||
        value === undefined ||
        value === "" ||
        value === "-"
    ) {

        return "—";

    }


    const number =
        Number(value);


    if (!Number.isFinite(number)) {
        return "—";
    }


    return number.toFixed(2);

}


function formatSigned(
    value
) {

    if (
        value === null ||
        value === undefined ||
        !Number.isFinite(
            Number(value)
        )
    ) {

        return "—";

    }


    const number =
        Number(value);


    return (
        number >= 0
            ? "+"
            : ""
    ) +
        number.toFixed(2);

}


function formatSignedPercent(
    value
) {

    if (
        value === null ||
        value === undefined ||
        !Number.isFinite(
            Number(value)
        )
    ) {

        return "—";

    }


    const number =
        Number(value);


    return (
        number >= 0
            ? "+"
            : ""
    ) +
        number.toFixed(2) +
        "%";

}


function formatVolume(
    value
) {

    if (
        value === null ||
        value === undefined ||
        !Number.isFinite(
            Number(value)
        )
    ) {

        return "—";

    }


    const number =
        Number(value);


    if (
        Math.abs(number) >=
        100000000
    ) {

        return (
            number /
            100000000
        ).toFixed(2) +
            "亿";

    }


    if (
        Math.abs(number) >=
        10000
    ) {

        return (
            number /
            10000
        ).toFixed(2) +
            "万";

    }


    return number.toFixed(0);

}


function formatAmount(
    value
) {

    if (
        value === null ||
        value === undefined ||
        !Number.isFinite(
            Number(value)
        )
    ) {

        return "—";

    }


    const number =
        Number(value);


    if (
        Math.abs(number) >=
        100000000
    ) {

        return (
            number /
            100000000
        ).toFixed(2) +
            "亿";

    }


    if (
        Math.abs(number) >=
        10000
    ) {

        return (
            number /
            10000
        ).toFixed(2) +
            "万";

    }


    return number.toFixed(2);

}


/* =========================================================
   清空图表
========================================================= */

function clearChart() {

    if (!chart) {
        return;
    }

    chart.clear();

}


/* =========================================================
   Loading
========================================================= */

function showLoading() {

    document
        .getElementById("loading")
        .classList.remove(
            "hidden"
        );

}


function hideLoading() {

    document
        .getElementById("loading")
        .classList.add(
            "hidden"
        );

}


/* =========================================================
   Status
========================================================= */

function showStatus(
    text
) {

    document
        .getElementById(
            "chartStatus"
        )
        .textContent = text;

}
