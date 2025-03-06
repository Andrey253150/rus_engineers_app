document.addEventListener("DOMContentLoaded", function () {
    console.log("JS файл загружен успешно!"); // Эта строка должна появиться в консоли браузера

    const logFilter = document.getElementById("log-filter");
    if (logFilter) {
        logFilter.addEventListener("change", function () {
            let filter = this.value;
            let logs = document.querySelectorAll(".log-entry");

            logs.forEach(log => {
                if (filter === "all") {
                    log.style.display = "block"; // Показать все
                } else if (log.classList.contains(filter)) {
                    log.style.display = "block"; // Показать только выбранные
                } else {
                    log.style.display = "none";  // Скрыть остальные
                }
            });
        });
    }
});
