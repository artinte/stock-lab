/* =========================================================
   STOCK LAB · 股票搜索

   功能：
   1. 从 watchlist.json 加载股票列表
   2. 实时匹配股票代码和名称
   3. 显示搜索联想结果
   4. 支持键盘上下键选择
   5. 支持 Enter 打开股票详情
   6. 点击查询按钮打开第一个匹配结果
   7. 通过 openStock() 统一跳转股票详情页
========================================================= */


/* =========================================================
   搜索配置
========================================================= */

const STOCK_LAB_BASE =
    window.location.hostname === "artinte.github.io"
        ? "/stock-lab"
        : "";


const STOCK_SEARCH_CONFIG = {

    // Watchlist 数据文件路径
    watchlistUrl:
        `${STOCK_LAB_BASE}/data/stock_watchlist.json`,

    // 最多显示的搜索结果数量
    maxResults: 8

};


/* =========================================================
   搜索状态
========================================================= */

const stockSearchState = {

    // Watchlist 股票列表
    watchlist: [],

    // 当前搜索结果
    results: [],

    // 当前键盘选中索引
    activeIndex: -1,

    // 是否加载完成
    loaded: false,

    // 是否正在加载
    loading: false

};


/* =========================================================
   初始化股票搜索
========================================================= */

async function initStockSearch() {

    const input =
        document.getElementById("stockSearch");

    const button =
        document.getElementById("stockSearchButton");

    const resultContainer =
        document.getElementById("stockSearchResults");


    if (
        !input ||
        !button ||
        !resultContainer
    ) {
        return;
    }


    // 加载 Watchlist
    await loadStockWatchlist();


    // 输入时实时搜索
    input.addEventListener(
        "input",
        searchStockPage
    );


    // 键盘交互
    input.addEventListener(
        "keydown",
        handleStockSearchKeydown
    );


    // 输入框获得焦点时恢复搜索结果
    input.addEventListener(
        "focus",
        () => {

            if (input.value.trim()) {
                searchStockPage();
            }

        }
    );


    // 点击页面其他区域时关闭搜索结果
    document.addEventListener(
        "click",
        event => {

            if (
                !event.target.closest(
                    ".stock-search-section"
                )
            ) {

                hideStockSearchResults();

            }

        }
    );

}


/* =========================================================
   加载 Watchlist
========================================================= */

async function loadStockWatchlist() {

    if (
        stockSearchState.loading ||
        stockSearchState.loaded
    ) {
        return;
    }


    stockSearchState.loading = true;


    try {

        const response =
            await fetch(
                STOCK_SEARCH_CONFIG.watchlistUrl
            );


        if (!response.ok) {

            throw new Error(
                `Watchlist 加载失败：${response.status}`
            );

        }


        const data =
            await response.json();


        if (!Array.isArray(data)) {

            throw new Error(
                "Watchlist 数据格式错误"
            );

        }


        // 标准化股票数据
        stockSearchState.watchlist =
            data
                .filter(stock => {

                    return (
                        stock &&
                        stock.symbol &&
                        stock.name
                    );

                })
                .map(stock => {

                    return {

                        symbol: String(
                            stock.symbol
                        ).trim(),

                        name: String(
                            stock.name
                        ).trim()

                    };

                })
                .filter(stock => {

                    return (
                        stock.symbol &&
                        stock.name
                    );

                });


        stockSearchState.loaded = true;


        console.log(
            `[Stock Search] 已加载 ${stockSearchState.watchlist.length} 只股票`
        );

    } catch (error) {

        console.error(
            "[Stock Search] Watchlist 加载失败：",
            error
        );


        stockSearchState.watchlist = [];

        stockSearchState.loaded = false;

    } finally {

        stockSearchState.loading = false;

    }

}


/* =========================================================
   搜索股票

   支持：
   1. 股票代码模糊匹配
   2. 股票名称模糊匹配
   3. 优先显示以关键词开头的结果
========================================================= */

function searchStockPage() {

    const input =
        document.getElementById(
            "stockSearch"
        );

    const resultContainer =
        document.getElementById(
            "stockSearchResults"
        );


    if (
        !input ||
        !resultContainer
    ) {
        return;
    }


    const keyword =
        input.value
            .trim()
            .toLowerCase();


    // 重置键盘选中状态
    stockSearchState.activeIndex = -1;


    // 输入为空时隐藏结果
    if (!keyword) {

        stockSearchState.results = [];

        hideStockSearchResults();

        return;

    }


    // Watchlist 尚未加载完成
    if (!stockSearchState.loaded) {

        resultContainer.innerHTML = `

            <div class="search-loading">
                股票数据加载中...
            </div>

        `;

        showStockSearchResults();

        return;

    }


    // 根据代码和名称进行匹配
    const results =
        stockSearchState.watchlist.filter(
            stock => {

                const symbol =
                    stock.symbol.toLowerCase();

                const name =
                    stock.name.toLowerCase();


                return (

                    symbol.includes(keyword)

                    ||

                    name.includes(keyword)

                );

            }
        );


    // 优先显示代码或名称以关键词开头的股票
    results.sort((a, b) => {

        const aStartsWith =
            a.symbol.toLowerCase().startsWith(keyword) ||
            a.name.toLowerCase().startsWith(keyword);

        const bStartsWith =
            b.symbol.toLowerCase().startsWith(keyword) ||
            b.name.toLowerCase().startsWith(keyword);


        if (
            aStartsWith !== bStartsWith
        ) {

            return aStartsWith ? -1 : 1;

        }


        return a.symbol.localeCompare(
            b.symbol
        );

    });


    // 限制搜索结果数量
    stockSearchState.results =
        results.slice(
            0,
            STOCK_SEARCH_CONFIG.maxResults
        );


    // 渲染结果
    renderStockSearchResults(
        stockSearchState.results
    );

}


/* =========================================================
   渲染搜索结果
========================================================= */

function renderStockSearchResults(results) {

    const resultContainer =
        document.getElementById(
            "stockSearchResults"
        );


    if (!resultContainer) {
        return;
    }


    // 没有匹配结果
    if (
        !results ||
        results.length === 0
    ) {

        resultContainer.innerHTML = `

            <div class="search-empty">

                <strong>
                    没有找到相关股票
                </strong>

                <p>
                    可以尝试输入股票代码或股票名称。
                </p>

            </div>

        `;


        showStockSearchResults();

        return;

    }


    // 渲染搜索列表
    resultContainer.innerHTML =
        results
            .map((stock, index) => {

                return createSearchResult(
                    stock,
                    index
                );

            })
            .join("");


    showStockSearchResults();

}


/* =========================================================
   创建单条搜索结果
========================================================= */

function createSearchResult(stock, index) {

    const symbol =
        escapeStockSearchHtml(
            stock.symbol
        );

    const name =
        escapeStockSearchHtml(
            stock.name
        );


    return `

        <button
            class="stock-search-result"
            type="button"
            role="option"
            aria-selected="false"
            data-index="${index}"
            data-symbol="${symbol}"
        >

            <div class="stock-search-result-main">

                <strong class="stock-search-result-name">
                    ${name}
                </strong>

                <span class="stock-search-result-symbol">
                    ${symbol}
                </span>

            </div>


            <div class="stock-search-result-action">

                <span>
                    查看详情
                </span>

                <span class="stock-search-result-arrow">
                    →
                </span>

            </div>

        </button>

    `;

}


/* =========================================================
   HTML 转义
========================================================= */

function escapeStockSearchHtml(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");

}


/* =========================================================
   显示搜索结果
========================================================= */

function showStockSearchResults() {

    const resultContainer =
        document.getElementById(
            "stockSearchResults"
        );

    const input =
        document.getElementById(
            "stockSearch"
        );


    if (!resultContainer) {
        return;
    }


    resultContainer.classList.add(
        "show"
    );


    if (input) {

        input.setAttribute(
            "aria-expanded",
            "true"
        );

    }

}


/* =========================================================
   隐藏搜索结果
========================================================= */

function hideStockSearchResults() {

    const resultContainer =
        document.getElementById(
            "stockSearchResults"
        );

    const input =
        document.getElementById(
            "stockSearch"
        );


    if (!resultContainer) {
        return;
    }


    resultContainer.classList.remove(
        "show"
    );


    if (input) {

        input.setAttribute(
            "aria-expanded",
            "false"
        );

    }


    stockSearchState.activeIndex = -1;

}


/* =========================================================
   点击搜索结果

   使用事件委托统一处理。
========================================================= */

document.addEventListener(
    "click",
    event => {

        const result =
            event.target.closest(
                ".stock-search-result"
            );


        if (!result) {
            return;
        }


        const symbol =
            result.dataset.symbol;


        if (symbol) {

            openStock(symbol);

        }

    }
);


/* =========================================================
   键盘交互

   ↑ / ↓：选择搜索结果
   Enter：打开选中股票
   Escape：关闭搜索结果
========================================================= */

function handleStockSearchKeydown(event) {

    const results =
        stockSearchState.results;


    // 没有搜索结果时，Enter 交给查询逻辑处理
    if (results.length === 0) {

        if (event.key === "Enter") {

            event.preventDefault();

            searchStockPage();

            const firstResult =
                stockSearchState.results[0];

            if (firstResult) {

                openStock(
                    firstResult.symbol
                );

            }

        }

        return;

    }


    // 向下选择
    if (event.key === "ArrowDown") {

        event.preventDefault();


        stockSearchState.activeIndex =
            (
                stockSearchState.activeIndex + 1
            ) % results.length;


        updateActiveStockSearchResult();

    }


    // 向上选择
    else if (event.key === "ArrowUp") {

        event.preventDefault();


        stockSearchState.activeIndex =
            stockSearchState.activeIndex <= 0

                ? results.length - 1

                : stockSearchState.activeIndex - 1;


        updateActiveStockSearchResult();

    }


    // Enter 打开当前选中的股票
    else if (event.key === "Enter") {

        event.preventDefault();


        const index =
            stockSearchState.activeIndex;


        const stock =
            index >= 0
                ? results[index]
                : results[0];


        if (stock) {

            openStock(
                stock.symbol
            );

        }

    }


    // Escape 关闭结果
    else if (event.key === "Escape") {

        hideStockSearchResults();

    }

}


/* =========================================================
   更新键盘选中状态
========================================================= */

function updateActiveStockSearchResult() {

    const resultContainer =
        document.getElementById(
            "stockSearchResults"
        );


    if (!resultContainer) {
        return;
    }


    const items =
        resultContainer.querySelectorAll(
            ".stock-search-result"
        );


    items.forEach((item, index) => {

        const active =
            index === stockSearchState.activeIndex;


        item.classList.toggle(
            "active",
            active
        );


        item.setAttribute(
            "aria-selected",
            String(active)
        );

    });


    // 滚动到当前选中项
    const activeItem =
        items[
            stockSearchState.activeIndex
        ];


    if (activeItem) {

        activeItem.scrollIntoView({
            block: "nearest"
        });

    }

}


/* =========================================================
   打开股票详情
========================================================= */

function openStock(symbol) {

    if (!symbol) {
        return;
    }


    hideStockSearchResults();


    window.location.href =
        `./detail.html?symbol=${encodeURIComponent(symbol)}`;

}


/* =========================================================
   初始化
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    initStockSearch
);