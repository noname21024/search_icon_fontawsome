document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const iconGrid = document.getElementById('iconGrid');
    let icons = [];
    let currentPage = 1; 
    const iconsPerPage = 100; 
    let totalPages = 0; 
    let filteredIcons = []; 

    fetch('metadata/icons.json')
        .then(response => response.json())
        .then(data => {
            // Process data to get free icons (solid, regular, brands)
            for (const [name, iconData] of Object.entries(data)) {
                if (iconData.free && iconData.free.length > 0) {
                    iconData.free.forEach(style => {
                        icons.push({
                            name: name,
                            label: iconData.label,
                            style: style, 
                            prefix: `fa-${style}`  
                        });
                    });
                }
            }
            filteredIcons = icons;
            totalPages = Math.ceil(filteredIcons.length / iconsPerPage);
            displayIconsForPage(currentPage);
            renderPagination();
        })
        .catch(error => console.error('Error loading icons:', error));

    // Search event listener
    searchInput.addEventListener('input', () => {
        const query = searchInput.value.toLowerCase();
        filteredIcons = icons.filter(icon => 
            icon.name.toLowerCase().includes(query) || icon.label.toLowerCase().includes(query)
        );
        totalPages = Math.ceil(filteredIcons.length / iconsPerPage); // Cập nhật tổng trang
        currentPage = 1; // Reset về trang 1
        displayIconsForPage(currentPage);
        renderPagination();
    });

    // Function to display icons in grid
    function displayIconsForPage(page) {
        iconGrid.innerHTML = '';  // Clear grid
        const start = (page - 1) * iconsPerPage;
        const end = start + iconsPerPage;
        const pageIcons = filteredIcons.slice(start, end);

        pageIcons.forEach(icon => {
            const card = document.createElement('div');
            card.classList.add('icon-card');

            const iconElement = document.createElement('i');
            iconElement.classList.add(icon.prefix, `${icon.prefix.split('-')[0]}-${icon.name}`);  

            const name = document.createElement('p');
            name.textContent = `${icon.name}`;

            const copied = document.createElement("p");
            copied.classList.add("copied");
            copied.textContent = "Đã copy code";

            // Append copied vào card ngay từ đầu (ẩn bằng CSS)
            card.appendChild(copied);

            // Sự kiện click trên card để copy
            card.addEventListener("click", () => {
                const htmlCode = `<i class="${icon.prefix} ${icon.prefix.split('-')[0]}-${icon.name}"></i>`;
                navigator.clipboard.writeText(htmlCode)
                    .then(() => {
                        copied.classList.add('active');  // Hiển thị thông báo
                        setTimeout(() => {
                            copied.classList.remove('active');  // Ẩn sau 1 giây
                        }, 1000);
                    })
                    .catch(err => console.error('Copy failed:', err));
            });

            card.appendChild(iconElement);
            card.appendChild(name);
            iconGrid.appendChild(card);
        });
    }
    function renderPagination(){
        const paginationContainer = document.getElementById("pagination");
        if(!paginationContainer) return;

        paginationContainer.innerHTML = '';

        const prevButton = document.createElement("button");
        prevButton.innerHTML = '<i class="fa-solid fa-arrow-left"></i>';
        prevButton.disabled = currentPage === 1;
        prevButton.addEventListener("click", ()=>{
            if (currentPage > 1) {  // Thêm if để an toàn, dù disabled
                currentPage--;
                displayIconsForPage(currentPage);
                renderPagination();
            }
        });
        paginationContainer.appendChild(prevButton);

        const pageInfo = document.createElement('span');
        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
        pageInfo.style.cursor = "pointer"; // Làm span clickable
        pageInfo.style.userSelect = "none"; // Tránh chọn text khi click
        paginationContainer.appendChild(pageInfo);

        // Event click để kích hoạt input
        pageInfo.addEventListener("click", () => {
            inputPage(currentPage, pageInfo, paginationContainer, totalPages);
        });

        const nextButton = document.createElement("button");
        nextButton.innerHTML = '<i class="fa-solid fa-arrow-right"></i>';
        nextButton.disabled = currentPage === totalPages;
        nextButton.addEventListener("click", ()=>{
            if(currentPage < totalPages){
                currentPage++;
                displayIconsForPage(currentPage);
                renderPagination()
            }
        });
        paginationContainer.appendChild(nextButton);
    };

    function inputPage(currentPageParam, pageInfo, paginationContainer, totalPages) {
        pageInfo.style.display = "none";
        const inputPage = document.createElement("input");
        inputPage.type = 'number';
        inputPage.value = currentPageParam;
        inputPage.classList.add('pagination-input');
        inputPage.min = 1;
        inputPage.max = totalPages; 

        paginationContainer.insertBefore(inputPage, pageInfo.nextSibling); // Giữ vị trí chính xác
        inputPage.focus(); 
        inputPage.select();

        function handleInputEnd(newPage) {
            let validPage = Math.max(1, Math.min(totalPages, parseInt(newPage) || currentPage));
            if (validPage !== currentPage) {
                currentPage = validPage;
                displayIconsForPage(currentPage);
            }
            inputPage.remove();
            // Không cập nhật pageInfo thủ công nữa, vì renderPagination sẽ tái tạo
            renderPagination();  // Gọi cuối cùng để làm mới toàn bộ
        }

        inputPage.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                handleInputEnd(inputPage.value);
            }
        });

        inputPage.addEventListener("blur", () => {
            handleInputEnd(inputPage.value);
        });

        // Thêm validate realtime (tùy chọn)
        inputPage.addEventListener("input", () => {
            if (inputPage.value < 1) inputPage.value = 1;
            if (inputPage.value > totalPages) inputPage.value = totalPages;
        });
    }
});