
/* =========================================================
   STOCK LAB 全局页面导航
========================================================= */

function goHome(page = "home") {
    window.location.href =
        `../?page=${page}`;
}


function navigatePage(page) {

    const routes = {

        home: "../",
        market: "../market",
        stock: "../stock/",
        news: "../news/",
        research: "../research/",
        trade: "../trade/",
        tools: "../tools/",
        document: "../document/"

    };

    const url = routes[page];

    if (!url) {

        console.error(
            `未知页面: ${page}`
        );

        return;

    }

    window.location.href = url;

}
