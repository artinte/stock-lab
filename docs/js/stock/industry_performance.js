/* ===============================================================
   STOCK LAB · Industry Performance

   FastAPI：

       GET /api/industry/performance

       参数：
           date
           level
           method


       GET /api/industry/performance/range

       参数：
           start_date
           end_date
           level
           method


   当前前端职责：

       API
          ↓
       获取当前层级行业数据
          ↓
       当前层级行业筛选
          ↓
       搜索
          ↓
       排序
          ↓
       页面展示


   后端负责：

       行业行情计算
       加权 / 等权
       JSON Cache

   =============================================================== */


/* ===============================================================
   State
   =============================================================== */

const state = {

    /*
     * 默认一级行业。
     *
     * 如果希望页面一进入就是二级行业，
     * 这里改成 2 即可。
     */
    level: 2,

    /*
     * 当前层级行业。
     *
     * 二级行业默认选择半导体。
     */
    industry: "半导体",

    period: 1,

    method: "weighted",

    search: "",

    sort: "desc",

    selectedCode: null,

    customStart: null,

    customEnd: null,

    data: {

        date: null,

        update_time: null,

        industries: []

    }

};


/* ===============================================================
   DOM
   =============================================================== */

const levelSelect =
    document.getElementById("levelSelect");

const industrySelect =
    document.getElementById("industrySelect");

const periodSelect =
    document.getElementById("periodSelect");

const searchInput =
    document.getElementById("searchInput");

const refreshButton =
    document.getElementById("refreshButton");

const customDateArea =
    document.getElementById("customDateArea");

const startDate =
    document.getElementById("startDate");

const endDate =
    document.getElementById("endDate");

const industryTable =
    document.getElementById("industryTable");

const detailContent =
    document.getElementById("detailContent");


/* ===============================================================
   Helpers
   =============================================================== */


/**
 * 格式化百分比
 */
function formatPct(value) {

    if (
        value === null ||
        value === undefined ||
        Number.isNaN(Number(value))
    ) {

        return "--";

    }

    const number =
        Number(value);


    if (number > 0) {

        return "+" +
            number.toFixed(2) +
            "%";

    }


    if (number < 0) {

        return number.toFixed(2) +
            "%";

    }


    return "0.00%";

}


/**
 * 涨跌颜色
 */
function pctClass(value) {

    const number =
        Number(value);


    if (number > 0) {

        return "up";

    }


    if (number < 0) {

        return "down";

    }


    return "flat";

}


/**
 * 行业层级名称
 */
function levelName(level) {

    const names = {

        1: "一级",
        2: "二级",
        3: "三级",
        4: "四级"

    };


    return names[level] || "";

}


/**
 * HTML 转义
 */
function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


/**
 * 获取今天日期
 *
 * YYYY-MM-DD
 */
function getToday() {

    const now =
        new Date();


    const year =
        now.getFullYear();


    const month =
        String(
            now.getMonth() + 1
        ).padStart(2, "0");


    const day =
        String(
            now.getDate()
        ).padStart(2, "0");


    return `${year}-${month}-${day}`;

}


/**
 * 获取过去 N 天日期
 */
function getDateBefore(
    dateString,
    days
) {

    const date =
        new Date(
            `${dateString}T00:00:00`
        );


    date.setDate(
        date.getDate() - days
    );


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


/* ===============================================================
   Industry Options
   =============================================================== */


/**
 * 根据当前已经加载的数据，
 * 生成当前层级行业选择器。
 *
 * 不请求 /api/industry/categories。
 *
 * 例如：
 *
 * level = 2
 *
 * → 从 state.data.industries 中提取二级行业
 *
 * 默认二级行业选择：
 *
 * 半导体
 */
function renderIndustryOptions() {

    const targetLevel =
        Number(state.level);


    if (!industrySelect) {

        return;

    }


    const industries =
        state.data.industries
            .filter(
                item =>
                    Number(item.level) ===
                    targetLevel
            )
            .sort(
                (a, b) =>
                    String(a.name)
                        .localeCompare(
                            String(b.name),
                            "zh-CN"
                        )
            );


    const currentIndustry =
        state.industry;


    industrySelect.innerHTML = `

        <option value="all">
            全部行业
        </option>

        ${industries.map(item => `

            <option
                value="${escapeHtml(item.code)}"
            >
                ${escapeHtml(item.name)}
            </option>

        `).join("")}

    `;


    /*
     * 如果当前行业仍然存在，
     * 保留当前选择。
     */

    const exists =
        industries.some(
            item =>
                String(item.code) ===
                String(currentIndustry)
        );


    if (exists) {

        industrySelect.value =
            currentIndustry;

        return;

    }


    /*
     * 第一次进入二级行业时，
     * 默认选择半导体。
     */

    if (targetLevel === 2) {

        const semiconductor =
            industries.find(
                item =>
                    item.name === "半导体"
            );


        if (semiconductor) {

            state.industry =
                semiconductor.code;

            industrySelect.value =
                semiconductor.code;

            return;

        }

    }


    /*
     * 当前层级没有半导体，
     * 默认显示全部行业。
     */

    state.industry =
        "all";

    industrySelect.value =
        "all";

}


/* ===============================================================
   API
   =============================================================== */


/**
 * 获取单日行业行情
 *
 * GET
 * /api/industry/performance
 */
async function fetchDailyData() {

    const params =
        new URLSearchParams();


    params.set(
        "level",
        state.level
    );


    params.set(
        "method",
        state.method
    );


    let date =
        getToday();


    if (
        state.period === "custom" &&
        state.customStart
    ) {

        date =
            state.customStart;

    }


    params.set(
        "date",
        date
    );


    const response =
        await fetch(
            `/api/industry/performance?${params.toString()}`,
            {
                method: "GET",
                headers: {
                    "Accept":
                        "application/json"
                }
            }
        );


    if (!response.ok) {

        throw new Error(
            `行业行情请求失败：HTTP ${response.status}`
        );

    }


    return await response.json();

}


/**
 * 获取区间行业行情
 *
 * GET
 * /api/industry/performance/range
 */
async function fetchRangeData(
    startDate,
    endDate
) {

    const params =
        new URLSearchParams();


    params.set(
        "start_date",
        startDate
    );


    params.set(
        "end_date",
        endDate
    );


    params.set(
        "level",
        state.level
    );


    params.set(
        "method",
        state.method
    );


    const response =
        await fetch(
            `/api/industry/performance/range?${params.toString()}`,
            {
                method: "GET",
                headers: {
                    "Accept":
                        "application/json"
                }
            }
        );


    if (!response.ok) {

        throw new Error(
            `行业区间行情请求失败：HTTP ${response.status}`
        );

    }


    return await response.json();

}


/* ===============================================================
   Load Data
   =============================================================== */


/**
 * 加载行业行情
 *
 * 1 日
 *     → /performance
 *
 * 5 / 20 / 60 / 120 日
 *     → /performance/range
 *
 * 自定义
 *     → /performance/range
 */
async function loadData() {

    try {

        let result;


        /* =====================================================
           单日
           ===================================================== */

        if (
            state.period === 1
        ) {

            result =
                await fetchDailyData();


            state.data = {

                date:
                    result.date,

                update_time:
                    result.update_time ||
                    null,

                industries:
                    result.industries || []

            };

        }


        /* =====================================================
           自定义日期
           ===================================================== */

        else if (
            state.period === "custom"
        ) {

            if (
                !state.customStart ||
                !state.customEnd
            ) {

                return;

            }


            result =
                await fetchRangeData(
                    state.customStart,
                    state.customEnd
                );


            state.data = {

                date:
                    `${result.start_date} ~ ${result.end_date}`,

                update_time:
                    null,

                industries:
                    result.industries || []

            };

        }


        /* =====================================================
           快捷区间
           ===================================================== */

        else {

            const endDate =
                getToday();


            const startDate =
                getDateBefore(
                    endDate,
                    Number(state.period) - 1
                );


            result =
                await fetchRangeData(
                    startDate,
                    endDate
                );


            state.data = {

                date:
                    `${result.start_date} ~ ${result.end_date}`,

                update_time:
                    null,

                industries:
                    result.industries || []

            };

        }


        /*
         * 数据加载完成后，
         * 根据当前 level 重新生成行业选择器。
         */

        renderIndustryOptions();

        renderTable();


        const dataDate =
            document.getElementById(
                "dataDate"
            );


        if (dataDate) {

            dataDate.textContent =
                state.data.date || "--";

        }


        const updateTime =
            document.getElementById(
                "updateTime"
            );


        if (updateTime) {

            updateTime.textContent =
                state.data.update_time || "--";

        }


    } catch (error) {

        console.error(
            "加载行业行情失败：",
            error
        );


        renderError(
            error.message
        );

    }

}


/* ===============================================================
   Error
   =============================================================== */

function renderError(message) {

    industryTable.innerHTML = `

        <tr>

            <td
                colspan="7"
                style="
                    height:180px;
                    text-align:center;
                    color:var(--text-muted);
                "
            >

                <div
                    style="
                        margin-bottom:8px;
                        font-weight:600;
                    "
                >
                    行业行情加载失败
                </div>

                <div
                    style="
                        font-size:12px;
                        opacity:.7;
                    "
                >
                    ${escapeHtml(message)}
                </div>

            </td>

        </tr>

    `;


    detailContent.innerHTML = `

        <div
            style="
                padding:40px;
                text-align:center;
                color:var(--text-muted);
            "
        >
            暂无行业详情
        </div>

    `;

}


/* ===============================================================
   Filter Data
   =============================================================== */

function getFilteredData() {

    let list =
        state.data.industries.filter(
            item =>
                Number(item.level) ===
                Number(state.level)
        );


    /*
     * 当前层级行业筛选。
     *
     * 注意：
     *
     * 这里不再使用 parent_code。
     *
     * 例如：
     *
     * state.industry = "半导体对应的 code"
     *
     * 就只显示半导体。
     */

    if (
        state.industry !== "all"
    ) {

        list =
            list.filter(
                item =>
                    String(item.code) ===
                    String(state.industry)
            );

    }


    /*
     * 搜索
     */

    if (
        state.search.trim()
    ) {

        const keyword =
            state.search
                .trim()
                .toLowerCase();


        list =
            list.filter(item => {

                return (

                    String(item.name)
                        .toLowerCase()
                        .includes(keyword)

                    ||

                    String(item.code)
                        .toLowerCase()
                        .includes(keyword)

                );

            });

    }


    /*
     * 排序
     */

    list.sort(
        (a, b) => {

            if (
                state.sort === "desc"
            ) {

                return (
                    Number(b.pct) -
                    Number(a.pct)
                );

            }


            return (
                Number(a.pct) -
                Number(b.pct)
            );

        }
    );


    return list;

}


/* ===============================================================
   Render Summary
   =============================================================== */

function renderSummary(list) {

    const count =
        list.length;


    const up =
        list.filter(
            item =>
                Number(item.pct) > 0
        ).length;


    const down =
        list.filter(
            item =>
                Number(item.pct) < 0
        ).length;


    const average =
        count
            ? list.reduce(
                (
                    sum,
                    item
                ) =>
                    sum +
                    Number(item.pct),
                0
            ) / count
            : 0;


    const industryCount =
        document.getElementById(
            "industryCount"
        );


    if (industryCount) {

        industryCount.textContent =
            count;

    }


    const upIndustryCount =
        document.getElementById(
            "upIndustryCount"
        );


    if (upIndustryCount) {

        upIndustryCount.textContent =
            up;

    }


    const downIndustryCount =
        document.getElementById(
            "downIndustryCount"
        );


    if (downIndustryCount) {

        downIndustryCount.textContent =
            down;

    }


    const averageElement =
        document.getElementById(
            "averagePct"
        );


    if (averageElement) {

        averageElement.textContent =
            formatPct(average);


        averageElement.className =
            "summary-value " +
            pctClass(average);

    }

}


/* ===============================================================
   Render Table
   =============================================================== */

function renderTable() {

    const list =
        getFilteredData();


    renderSummary(list);


    if (!list.length) {

        industryTable.innerHTML = `

            <tr>

                <td
                    colspan="7"
                    style="
                        height:180px;
                        text-align:center;
                        color:var(--text-muted);
                    "
                >
                    没有找到符合条件的行业
                </td>

            </tr>

        `;


        detailContent.innerHTML = `

            <div
                style="
                    padding:40px;
                    text-align:center;
                    color:var(--text-muted);
                "
            >
                暂无行业数据
            </div>

        `;

        return;

    }


    const maxAbs =
        Math.max(
            ...list.map(
                item =>
                    Math.abs(
                        Number(item.pct)
                    )
            ),
            1
        );


    industryTable.innerHTML =
        list.map(
            (item, index) => {

                const pct =
                    Number(item.pct);


                const width =
                    Math.min(
                        Math.abs(pct)
                        /
                        maxAbs
                        *
                        100,
                        100
                    );


                const barClass =
                    pct < 0
                        ? "bar-fill down"
                        : "bar-fill";


                return `

                    <tr
                        data-code="${escapeHtml(item.code)}"
                        class="industry-row"
                    >

                        <td>

                            <div class="industry-cell">

                                <span class="rank">
                                    ${index + 1}
                                </span>

                                <span
                                    class="level-badge"
                                >
                                    ${levelName(item.level)}
                                </span>

                                <div class="industry-info">

                                    <div
                                        class="industry-name"
                                    >
                                        ${escapeHtml(item.name)}
                                    </div>

                                    <div
                                        class="industry-code"
                                    >
                                        ${escapeHtml(item.code)}
                                    </div>

                                </div>

                            </div>

                        </td>


                        <td>

                            <span
                                class="pct ${pctClass(pct)}"
                            >
                                ${formatPct(pct)}
                            </span>

                        </td>


                        <td>

                            <span class="count-up">
                                ${item.up ?? "--"}
                            </span>

                        </td>


                        <td>

                            <span class="count-down">
                                ${item.down ?? "--"}
                            </span>

                        </td>


                        <td>
                            ${item.stocks ?? "--"}
                        </td>


                        <td class="bar-cell">

                            <div class="bar">

                                <div
                                    class="${barClass}"
                                    style="
                                        width:${width}%;
                                    "
                                ></div>

                            </div>

                        </td>


                        <td>

                            <button
                                class="expand-button"
                                data-detail="${escapeHtml(item.code)}"
                                title="查看详情"
                                type="button"
                            >
                                →
                            </button>

                        </td>

                    </tr>

                `;

            }
        ).join("");


    /*
     * 详情按钮
     */

    document
        .querySelectorAll(
            "[data-detail]"
        )
        .forEach(button => {

            button.addEventListener(
                "click",
                event => {

                    event.stopPropagation();


                    const code =
                        button.dataset.detail;


                    selectIndustry(code);

                }
            );

        });


    /*
     * 行点击
     */

    document
        .querySelectorAll(
            ".industry-row"
        )
        .forEach(row => {

            row.addEventListener(
                "click",
                () => {

                    selectIndustry(
                        row.dataset.code
                    );

                }
            );

        });


    /*
     * 自动选择第一项
     */

    if (
        !state.selectedCode ||
        !list.some(
            item =>
                item.code ===
                state.selectedCode
        )
    ) {

        selectIndustry(
            list[0].code
        );

    } else {

        selectIndustry(
            state.selectedCode
        );

    }

}


/* ===============================================================
   History
   =============================================================== */

function generateHistory(
    basePct
) {

    const result = [];

    let current = 0;


    for (
        let i = 0;
        i < 20;
        i++
    ) {

        const random =
            (
                Math.random() -
                0.46
            ) * 0.8;


        current += random;


        if (
            i === 19
        ) {

            current =
                Number(basePct);

        }


        result.push({

            date:
                String(i + 1)
                    .padStart(2, "0"),

            pct:
                current

        });

    }


    return result;

}


/* ===============================================================
   SVG Chart
   =============================================================== */

function renderChart(history) {

    const width = 560;

    const height = 190;

    const padding = {

        left: 12,

        right: 12,

        top: 12,

        bottom: 22

    };


    const values =
        history.map(
            item =>
                Number(item.pct)
        );


    const max =
        Math.max(
            ...values,
            1
        );


    const min =
        Math.min(
            ...values,
            -1
        );


    const range =
        Math.max(
            max - min,
            2
        );


    function x(index) {

        return (
            padding.left
            +
            index
            /
            (history.length - 1)
            *
            (
                width
                -
                padding.left
                -
                padding.right
            )
        );

    }


    function y(value) {

        return (
            padding.top
            +
            (
                max - value
            )
            /
            range
            *
            (
                height
                -
                padding.top
                -
                padding.bottom
            )
        );

    }


    const points =
        history.map(
            (
                item,
                index
            ) =>
                `${x(index)},${y(item.pct)}`
        );


    const line =
        points.join(" ");


    const area =
        `
        ${points.join(" ")}
        ${x(history.length - 1)},${height - padding.bottom}
        ${x(0)},${height - padding.bottom}
        `;


    const zeroY =
        y(0);


    const first =
        history[0];


    const last =
        history[
        history.length - 1
        ];


    return `

        <svg
            class="chart"
            viewBox="0 0 ${width} ${height}"
            preserveAspectRatio="none"
        >

            <line
                class="chart-grid"
                x1="0"
                y1="${padding.top}"
                x2="${width}"
                y2="${padding.top}"
            />

            <line
                class="chart-zero"
                x1="0"
                y1="${zeroY}"
                x2="${width}"
                y2="${zeroY}"
            />

            <line
                class="chart-grid"
                x1="0"
                y1="${height - padding.bottom}"
                x2="${width}"
                y2="${height - padding.bottom}"
            />


            <polygon
                class="chart-area"
                points="${area}"
            />


            <polyline
                class="chart-line"
                points="${line}"
            />


            <circle
                class="chart-point"
                cx="${x(history.length - 1)}"
                cy="${y(last.pct)}"
                r="4"
            />


            <text
                class="chart-label"
                x="${padding.left}"
                y="${height - 5}"
            >
                ${escapeHtml(first.date)}
            </text>


            <text
                class="chart-label"
                text-anchor="end"
                x="${width - padding.right}"
                y="${height - 5}"
            >
                ${escapeHtml(last.date)}
            </text>

        </svg>

    `;

}


/* ===============================================================
   Select Industry
   =============================================================== */

function selectIndustry(code) {

    const item =
        state.data.industries.find(
            item =>
                item.code === code
        );


    if (!item) {

        return;

    }


    state.selectedCode =
        code;


    const history =
        item.history &&
            item.history.length
            ? item.history
            : generateHistory(
                item.pct
            );


    const total =
        Number(item.stocks) || 0;


    const up =
        Number(item.up) || 0;


    const down =
        Number(item.down) || 0;


    const flat =
        Number(item.flat) || 0;


    const upPct =
        total
            ? up / total * 100
            : 0;


    const downPct =
        total
            ? down / total * 100
            : 0;


    const flatPct =
        total
            ? flat / total * 100
            : 0;


    detailContent.innerHTML = `

        <div class="detail-head">

            <div>

                <div class="detail-name">
                    ${escapeHtml(item.name)}
                </div>

                <div class="detail-code">
                    ${escapeHtml(item.code)}
                    ·
                    ${levelName(item.level)}行业
                </div>

            </div>


            <div class="detail-pct">

                <div
                    class="
                        detail-pct-value
                        ${pctClass(item.pct)}
                    "
                >
                    ${formatPct(item.pct)}
                </div>

                <div class="detail-pct-label">

                    ${state.period === 1
            ? "当日涨跌"
            : "区间涨跌"
        }

                </div>

            </div>

        </div>


        <div class="chart-card">

            <div class="chart-header">

                <div class="chart-title">
                    区间走势
                </div>

                <div class="chart-period">

                    ${state.period === 1
            ? "当日"
            : state.period === "custom"
                ? `${state.customStart || "--"} ~ ${state.customEnd || "--"}`
                : `近 ${state.period} 个交易日`
        }

                </div>

            </div>


            ${renderChart(history)}

        </div>


        <div class="detail-stats">


            <div class="detail-stat">

                <div class="detail-stat-label">
                    成分股
                </div>

                <div class="detail-stat-value">
                    ${item.stocks ?? "--"}
                </div>

            </div>


            <div class="detail-stat">

                <div class="detail-stat-label">
                    上涨家数
                </div>

                <div
                    class="
                        detail-stat-value
                        count-up
                    "
                >
                    ${item.up ?? "--"}
                </div>

            </div>


            <div class="detail-stat">

                <div class="detail-stat-label">
                    下跌家数
                </div>

                <div
                    class="
                        detail-stat-value
                        count-down
                    "
                >
                    ${item.down ?? "--"}
                </div>

            </div>


            <div class="detail-stat">

                <div class="detail-stat-label">
                    平盘家数
                </div>

                <div class="detail-stat-value">
                    ${item.flat ?? "--"}
                </div>

            </div>


        </div>


        <div>

            <div class="distribution-title">
                成分股涨跌分布
            </div>


            <div class="distribution">

                <div
                    class="dist-up"
                    style="width:${upPct}%"
                ></div>

                <div
                    class="dist-flat"
                    style="width:${flatPct}%"
                ></div>

                <div
                    class="dist-down"
                    style="width:${downPct}%"
                ></div>

            </div>


            <div class="distribution-legend">

                <span>
                    上涨 ${item.up ?? "--"}
                </span>

                <span>
                    平盘 ${item.flat ?? "--"}
                </span>

                <span>
                    下跌 ${item.down ?? "--"}
                </span>

            </div>

        </div>

    `;

}


/* ===============================================================
   Level Change
   =============================================================== */

levelSelect.addEventListener(
    "change",
    () => {

        state.level =
            Number(
                levelSelect.value
            );


        /*
         * 切换层级后，
         * 让 renderIndustryOptions()
         * 根据新的层级重新选择行业。
         */

        state.industry =
            "all";


        state.selectedCode =
            null;


        loadData();

    }
);


/* ===============================================================
   Industry Change
   =============================================================== */

industrySelect.addEventListener(
    "change",
    () => {

        state.industry =
            industrySelect.value;


        state.selectedCode =
            null;


        /*
         * 行业选择只是前端筛选。
         *
         * 不重新请求 API。
         */

        renderTable();

    }
);


/* ===============================================================
   Period Select
   =============================================================== */

periodSelect.addEventListener(
    "change",
    () => {

        state.period =
            periodSelect.value === "custom"
                ? "custom"
                : Number(
                    periodSelect.value
                );


        customDateArea.style.display =
            state.period === "custom"
                ? "block"
                : "none";


        document
            .querySelectorAll(
                ".period-button"
            )
            .forEach(button => {

                button.classList.toggle(
                    "active",
                    button.dataset.period ===
                    String(state.period)
                );

            });


        if (
            state.period !== "custom"
        ) {

            state.selectedCode =
                null;


            loadData();

        }

    }
);


/* ===============================================================
   Quick Period
   =============================================================== */

document
    .querySelectorAll(
        ".period-button"
    )
    .forEach(button => {

        button.addEventListener(
            "click",
            () => {

                const period =
                    Number(
                        button.dataset.period
                    );


                state.period =
                    period;


                periodSelect.value =
                    String(period);


                customDateArea.style.display =
                    "none";


                document
                    .querySelectorAll(
                        ".period-button"
                    )
                    .forEach(item => {

                        item.classList.toggle(
                            "active",
                            item === button
                        );

                    });


                state.selectedCode =
                    null;


                loadData();

            }
        );

    });


/* ===============================================================
   Method
   =============================================================== */

document
    .querySelectorAll(
        ".method-button"
    )
    .forEach(button => {

        button.addEventListener(
            "click",
            () => {

                document
                    .querySelectorAll(
                        ".method-button"
                    )
                    .forEach(item => {

                        item.classList.remove(
                            "active"
                        );

                    });


                button.classList.add(
                    "active"
                );


                state.method =
                    button.dataset.method;


                state.selectedCode =
                    null;


                loadData();

            }
        );

    });


/* ===============================================================
   Search
   =============================================================== */

searchInput.addEventListener(
    "input",
    () => {

        state.search =
            searchInput.value;


        renderTable();

    }
);


/* ===============================================================
   Sort
   =============================================================== */

document
    .getElementById("sortButton")
    .addEventListener(
        "click",
        () => {

            state.sort =
                state.sort === "desc"
                    ? "asc"
                    : "desc";


            document.getElementById(
                "sortButton"
            ).textContent =
                state.sort === "desc"
                    ? "涨跌幅 ↓"
                    : "涨跌幅 ↑";


            renderTable();

        }
    );


/* ===============================================================
   Refresh
   =============================================================== */

refreshButton.addEventListener(
    "click",
    async () => {

        const originalText =
            refreshButton.textContent;


        refreshButton.textContent =
            "更新中...";


        refreshButton.disabled =
            true;


        try {

            await loadData();

        } finally {

            refreshButton.textContent =
                originalText;


            refreshButton.disabled =
                false;

        }

    }
);


/* ===============================================================
   Custom Dates
   =============================================================== */

startDate.addEventListener(
    "change",
    () => {

        state.customStart =
            startDate.value;


        if (
            state.customStart &&
            state.customEnd
        ) {

            state.selectedCode =
                null;


            loadData();

        }

    }
);


endDate.addEventListener(
    "change",
    () => {

        state.customEnd =
            endDate.value;


        if (
            state.customStart &&
            state.customEnd
        ) {

            state.selectedCode =
                null;


            loadData();

        }

    }
);


/* ===============================================================
   Initial
   =============================================================== */

/*
 * 页面默认：
 *
 * 二级行业
 * ↓
 * 半导体
 */

levelSelect.value =
    String(state.level);

loadData();