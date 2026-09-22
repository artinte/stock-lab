

/* ===============================================================
   STOCK LAB · Industry Performance
 
   当前：
       使用 mockData
 
   后续：
       将 loadData() 替换为 FastAPI 请求即可。
 
   推荐 API：
 
       GET /api/industry/performance
 
   参数：
 
       level
       parent
       period
       method
       start_date
       end_date
 
   例如：
 
       /api/industry/performance
           ?level=2
           &period=20
           &method=weighted
 
   =============================================================== */


/* ===============================================================
   Mock Data
   =============================================================== */

const mockData = {

    date: "2026-09-22",

    update_time: "2026-09-22 15:10",

    industries: [

        {
            code: "A01",
            name: "农林牧渔",
            level: 1,
            parent_code: null,
            pct: 2.18,
            stocks: 87,
            up: 61,
            down: 21,
            flat: 5
        },

        {
            code: "A02",
            name: "基础化工",
            level: 1,
            parent_code: null,
            pct: 1.64,
            stocks: 312,
            up: 224,
            down: 77,
            flat: 11
        },

        {
            code: "A03",
            name: "钢铁",
            level: 1,
            parent_code: null,
            pct: 0.72,
            stocks: 45,
            up: 29,
            down: 14,
            flat: 2
        },

        {
            code: "A04",
            name: "有色金属",
            level: 1,
            parent_code: null,
            pct: 2.84,
            stocks: 98,
            up: 77,
            down: 18,
            flat: 3
        },

        {
            code: "A05",
            name: "电子",
            level: 1,
            parent_code: null,
            pct: 1.93,
            stocks: 361,
            up: 260,
            down: 86,
            flat: 15
        },

        {
            code: "A06",
            name: "汽车",
            level: 1,
            parent_code: null,
            pct: 1.21,
            stocks: 183,
            up: 127,
            down: 49,
            flat: 7
        },

        {
            code: "A07",
            name: "机械设备",
            level: 1,
            parent_code: null,
            pct: 0.96,
            stocks: 265,
            up: 166,
            down: 89,
            flat: 10
        },

        {
            code: "A08",
            name: "医药生物",
            level: 1,
            parent_code: null,
            pct: -0.42,
            stocks: 318,
            up: 127,
            down: 177,
            flat: 14
        },

        {
            code: "A09",
            name: "食品饮料",
            level: 1,
            parent_code: null,
            pct: -0.76,
            stocks: 124,
            up: 39,
            down: 81,
            flat: 4
        },

        {
            code: "A10",
            name: "计算机",
            level: 1,
            parent_code: null,
            pct: 1.38,
            stocks: 282,
            up: 196,
            down: 76,
            flat: 10
        },

        {
            code: "A11",
            name: "传媒",
            level: 1,
            parent_code: null,
            pct: 0.53,
            stocks: 152,
            up: 91,
            down: 55,
            flat: 6
        },

        {
            code: "A12",
            name: "通信",
            level: 1,
            parent_code: null,
            pct: 2.37,
            stocks: 119,
            up: 89,
            down: 27,
            flat: 3
        },

        {
            code: "A13",
            name: "银行",
            level: 1,
            parent_code: null,
            pct: -0.18,
            stocks: 42,
            up: 16,
            down: 23,
            flat: 3
        },

        {
            code: "A14",
            name: "非银金融",
            level: 1,
            parent_code: null,
            pct: 0.34,
            stocks: 81,
            up: 44,
            down: 33,
            flat: 4
        },

        {
            code: "A15",
            name: "房地产",
            level: 1,
            parent_code: null,
            pct: -1.28,
            stocks: 108,
            up: 24,
            down: 78,
            flat: 6
        },

        {
            code: "A16",
            name: "建筑材料",
            level: 1,
            parent_code: null,
            pct: -0.34,
            stocks: 76,
            up: 30,
            down: 42,
            flat: 4
        },

        {
            code: "A17",
            name: "电力设备",
            level: 1,
            parent_code: null,
            pct: 1.76,
            stocks: 229,
            up: 167,
            down: 56,
            flat: 6
        },

        {
            code: "A18",
            name: "公用事业",
            level: 1,
            parent_code: null,
            pct: 0.18,
            stocks: 94,
            up: 45,
            down: 43,
            flat: 6
        },

        {
            code: "A19",
            name: "交通运输",
            level: 1,
            parent_code: null,
            pct: 0.62,
            stocks: 119,
            up: 70,
            down: 44,
            flat: 5
        },

        {
            code: "A20",
            name: "商贸零售",
            level: 1,
            parent_code: null,
            pct: -0.21,
            stocks: 109,
            up: 46,
            down: 57,
            flat: 6
        },

        {
            code: "A21",
            name: "社会服务",
            level: 1,
            parent_code: null,
            pct: 0.41,
            stocks: 68,
            up: 39,
            down: 26,
            flat: 3
        },

        {
            code: "A22",
            name: "美容护理",
            level: 1,
            parent_code: null,
            pct: -0.62,
            stocks: 31,
            up: 10,
            down: 19,
            flat: 2
        },

        {
            code: "A23",
            name: "家用电器",
            level: 1,
            parent_code: null,
            pct: 0.86,
            stocks: 92,
            up: 57,
            down: 31,
            flat: 4
        },

        {
            code: "A24",
            name: "纺织服饰",
            level: 1,
            parent_code: null,
            pct: -0.16,
            stocks: 87,
            up: 40,
            down: 42,
            flat: 5
        },

        {
            code: "A25",
            name: "轻工制造",
            level: 1,
            parent_code: null,
            pct: 0.37,
            stocks: 113,
            up: 62,
            down: 46,
            flat: 5
        },

        {
            code: "A26",
            name: "国防军工",
            level: 1,
            parent_code: null,
            pct: 2.06,
            stocks: 83,
            up: 63,
            down: 18,
            flat: 2
        },

        {
            code: "A27",
            name: "计算机应用",
            level: 1,
            parent_code: null,
            pct: 1.44,
            stocks: 141,
            up: 101,
            down: 36,
            flat: 4
        },

        {
            code: "A28",
            name: "综合",
            level: 1,
            parent_code: null,
            pct: 0.12,
            stocks: 37,
            up: 17,
            down: 18,
            flat: 2
        }

    ]

};


/* ===============================================================
   State
   =============================================================== */

const state = {

    level: 1,

    parent: "all",

    period: 1,

    method: "weighted",

    search: "",

    sort: "desc",

    selectedCode: null,

    customStart: null,

    customEnd: null,

    data: mockData

};


/* ===============================================================
   DOM
   =============================================================== */

const levelSelect =
    document.getElementById("levelSelect");

const parentSelect =
    document.getElementById("parentSelect");

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

function formatPct(value) {

    if (value === null || value === undefined) {
        return "--";
    }

    const number = Number(value);

    if (number > 0) {
        return "+" + number.toFixed(2) + "%";
    }

    if (number < 0) {
        return number.toFixed(2) + "%";
    }

    return "0.00%";
}


function pctClass(value) {

    if (value > 0) {
        return "up";
    }

    if (value < 0) {
        return "down";
    }

    return "flat";
}


function levelName(level) {

    const names = {
        1: "一级",
        2: "二级",
        3: "三级",
        4: "四级"
    };

    return names[level] || "";
}


function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/* ===============================================================
   Generate mock chart
   后续由 API 返回真实历史数据。
 
   推荐：
 
   history: [
       {
           date: "2026-09-01",
           pct: 1.21
       }
   ]
 
   =============================================================== */

function generateHistory(basePct) {

    const result = [];

    let current = 0;

    for (let i = 0; i < 20; i++) {

        const random =
            (Math.random() - 0.46) * 0.8;

        current += random;

        if (i === 19) {
            current = basePct;
        }

        result.push({
            date: `09-${String(i + 1).padStart(2, "0")}`,
            pct: current
        });
    }

    return result;
}


/* ===============================================================
   Filter Data
   =============================================================== */

function getFilteredData() {

    let list =
        state.data.industries
            .filter(item =>
                item.level === Number(state.level)
            );


    if (state.parent !== "all") {

        list =
            list.filter(
                item =>
                    item.parent_code === state.parent
            );
    }


    if (state.search.trim()) {

        const keyword =
            state.search
                .trim()
                .toLowerCase();

        list =
            list.filter(item => {

                return (
                    item.name
                        .toLowerCase()
                        .includes(keyword)
                    ||
                    item.code
                        .toLowerCase()
                        .includes(keyword)
                );

            });

    }


    list.sort((a, b) => {

        if (state.sort === "desc") {
            return b.pct - a.pct;
        }

        return a.pct - b.pct;

    });


    return list;
}


/* ===============================================================
   Render Parent Options
   =============================================================== */

function renderParentOptions() {

    const targetLevel =
        Number(state.level);

    if (targetLevel <= 1) {

        parentSelect.innerHTML = `
            <option value="all">
                全部行业
            </option>
        `;

        parentSelect.disabled = true;

        return;
    }


    parentSelect.disabled = false;


    const parentLevel =
        targetLevel - 1;


    const parents =
        state.data.industries
            .filter(
                item =>
                    item.level === parentLevel
            );


    parentSelect.innerHTML = `

        <option value="all">
            全部行业
        </option>

        ${parents.map(item => `

            <option value="${escapeHtml(item.code)}">
                ${escapeHtml(item.name)}
            </option>

        `).join("")}

    `;


    parentSelect.value =
        state.parent;
}


/* ===============================================================
   Render Summary
   =============================================================== */

function renderSummary(list) {

    const count =
        list.length;


    const up =
        list.filter(
            item => item.pct > 0
        ).length;


    const down =
        list.filter(
            item => item.pct < 0
        ).length;


    const average =
        count
            ? list.reduce(
                (sum, item) =>
                    sum + item.pct,
                0
            ) / count
            : 0;


    document.getElementById(
        "industryCount"
    ).textContent = count;


    document.getElementById(
        "upIndustryCount"
    ).textContent = up;


    document.getElementById(
        "downIndustryCount"
    ).textContent = down;


    const averageElement =
        document.getElementById(
            "averagePct"
        );


    averageElement.textContent =
        formatPct(average);


    averageElement.className =
        "summary-value " +
        pctClass(average);

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

        return;
    }


    const maxAbs =
        Math.max(
            ...list.map(
                item =>
                    Math.abs(item.pct)
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
                        / maxAbs
                        * 100,
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
                                ${item.up}
                            </span>

                        </td>


                        <td>

                            <span class="count-down">
                                ${item.down}
                            </span>

                        </td>


                        <td>
                            ${item.stocks}
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
                            >
                                →
                            </button>

                        </td>

                    </tr>

                `;

            }
        ).join("");


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

    if (!state.selectedCode ||
        !list.some(
            item =>
                item.code === state.selectedCode
        )
    ) {

        selectIndustry(
            list[0].code
        );

    }

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
            (item, index) =>
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
        history[history.length - 1];


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
                ${first.date}
            </text>


            <text
                class="chart-label"
                text-anchor="end"
                x="${width - padding.right}"
                y="${height - 5}"
            >
                ${last.date}
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
        generateHistory(
            item.pct
        );


    const total =
        item.stocks;


    const upPct =
        total
            ? item.up / total * 100
            : 0;


    const downPct =
        total
            ? item.down / total * 100
            : 0;


    const flatPct =
        total
            ? item.flat / total * 100
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
            : `近 ${state.period} 日涨跌`}
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
            : `近 ${state.period} 个交易日`}
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
                    ${item.stocks}
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
                    ${item.up}
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
                    ${item.down}
                </div>

            </div>


            <div class="detail-stat">

                <div class="detail-stat-label">
                    平盘家数
                </div>

                <div class="detail-stat-value">
                    ${item.flat}
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
                    上涨 ${item.up}
                </span>

                <span>
                    平盘 ${item.flat}
                </span>

                <span>
                    下跌 ${item.down}
                </span>

            </div>

        </div>

    `;

}


/* ===============================================================
   Load Data
   =============================================================== */

async function loadData() {

    /*
     * ============================================================
     * 未来接 FastAPI 时，主要修改这里。
     *
     * const params = new URLSearchParams({
     *
     *     level: state.level,
     *     parent: state.parent,
     *     period: state.period,
     *     method: state.method
     *
     * });
     *
     * if (state.period === "custom") {
     *
     *     params.set(
     *         "start_date",
     *         state.customStart
     *     );
     *
     *     params.set(
     *         "end_date",
     *         state.customEnd
     *     );
     *
     * }
     *
     * const response =
     *     await fetch(
     *         `/api/industry/performance?${params}`
     *     );
     *
     * state.data =
     *     await response.json();
     *
     * ============================================================
     */


    /*
     * MVP 阶段直接使用本地数据。
     */

    await new Promise(
        resolve =>
            setTimeout(resolve, 180)
    );


    state.data =
        mockData;


    document.getElementById(
        "dataDate"
    ).textContent =
        state.data.date;


    document.getElementById(
        "updateTime"
    ).textContent =
        state.data.update_time;


    renderParentOptions();

    renderTable();

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

        state.parent =
            "all";

        renderParentOptions();

        loadData();

    }
);


/* ===============================================================
   Parent Change
   =============================================================== */

parentSelect.addEventListener(
    "change",
    () => {

        state.parent =
            parentSelect.value;

        loadData();

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


        if (state.period !== "custom") {
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

            loadData();

        }

    }
);


/* ===============================================================
   Initial
   =============================================================== */

renderParentOptions();

renderTable();
