document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const iconGrid = document.getElementById('iconGrid');
    const versionIcons = document.getElementById("fontawesome_version");
    let icons = [];
    let currentPage = 1; 
    const iconsPerPage = 100; 
    let totalPages = 0; 
    let filteredIcons = []; 
    let totalIcons = 0;
    let currentVersion = localStorage.getItem('selectedVersion') || "7.1.0";  // Đọc từ LocalStorage, default 7.1.0

    const cdnLinks = {
        "5.15.4": '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" integrity="sha512-1ycn6IcaQQ40/MKBW2W4Rhis/DbILU74C1vSrLJxCq57o941Ym01SwNsOMqvEBFlcgUa6xLiPY/NS5R+E6ztJQ==" crossorigin="anonymous" referrerpolicy="no-referrer" />',
        "6.7.2": '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.7.2/css/all.min.css" integrity="sha512-Evv84Mr4kqVGRNSgIGL/F/aIDqQb7xQ2vcrdIwxfjThSH8CSR7PBEakCr51Ck+w+/U6swU2Im1vVX0SVk9ABhg==" crossorigin="anonymous" referrerpolicy="no-referrer" />',
        "7.1.0": '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/7.0.1/css/all.min.css" integrity="sha512-2SwdPD6INVrV/lHTZbO2nodKhrnDdJK9/kg2XD1r9uGqPo1cUbujc+IYdlYdEErWNu69gVcYgdxlmVmzTWnetw==" crossorigin="anonymous" referrerpolicy="no-referrer" />'
    };

    const zipPaths = {
        "5.15.4": "downloads/fontawesome-free-5.15.4-web.zip",
        "6.7.2": "downloads/fontawesome-free-6.7.2-web.zip",
        "7.1.0": "downloads/fontawesome-free-7.1.0-web.zip"
    };

    // Cập nhật select box với version lưu trữ
    versionIcons.value = currentVersion;

    updateFontAwesomeCss(currentVersion);
    fetchIcons(currentVersion);

    const downloadBtn = document.querySelector(".download-btn");
    downloadBtn.href = zipPaths[currentVersion] || zipPaths["7.1.0"];
    downloadBtn.download = `fontawesome-free-${currentVersion}-web.zip`;

    // Cập nhật icon search
    const searchIcon = document.querySelector('.search-container i');
    const searchClasses = getIconClasses('search', currentVersion);
    searchIcon.className = ''; // Xóa class cũ
    searchIcon.classList.add(...searchClasses);

    // Cập nhật icon scroll-to-top
    const scrollIcon = document.getElementById('scrollToTopBottom').querySelector('i');
    const scrollClasses = getIconClasses('arrow-up', currentVersion);
    scrollIcon.className = '';
    scrollIcon.classList.add(...scrollClasses);

    // Thêm logic copy CDN động (di chuyển từ HTML)
    const buttonCopyCDN = document.getElementById("copyCDN");
    const copyedCDN = document.querySelector(".copied-cnd");
    buttonCopyCDN.addEventListener("click", async () => {
        const cdn = cdnLinks[currentVersion] || cdnLinks["7.1.0"];
        copyedCDN.classList.add('active');
        await navigator.clipboard.writeText(cdn);
        setTimeout(() => {
            copyedCDN.classList.remove("active");
        }, 1500);
    });

    function updateFontAwesomeCss(version){
        const link = document.getElementById("fontawesomeCss");
        link.href = `data/fontawesome-free-${version}-web/css/all.css`
    }

    // hàm lấy version của fontaswesome
    versionIcons.addEventListener("change", function(){
        currentVersion = this.value;
        localStorage.setItem('selectedVersion', currentVersion);  // Lưu vào LocalStorage
        currentPage = 1;
        updateFontAwesomeCss(currentVersion);
        fetchIcons(currentVersion);
        downloadBtn.href = zipPaths[currentVersion] || zipPaths["7.1.0"];
        downloadBtn.download = `fontawesome-free-${currentVersion}-web.zip`;

        // Cập nhật icon search
        const searchIcon = document.querySelector('.search-container i');
        const searchClasses = getIconClasses('search', currentVersion);
        searchIcon.className = ''; // Xóa class cũ
        searchIcon.classList.add(...searchClasses);

        // Cập nhật icon scroll-to-top
        const scrollIcon = document.getElementById('scrollToTopBottom').querySelector('i');
        const scrollClasses = getIconClasses('arrow-up', currentVersion);
        scrollIcon.className = '';
        scrollIcon.classList.add(...scrollClasses);
    })
    
    // hàm lấy icon từ folder
    function getStylePrefix(style, version) {
        const majorVer = parseInt(version.split('.')[0]);
        if (majorVer <= 5) {
            // v5: solid → fas, regular → far, brands → fab
            return style === 'solid' ? 'fas' :
                style === 'regular' ? 'far' :
                style === 'brands' ? 'fab' : 'fas';
        } else {
            // v6+: solid → fa-solid, ...
            return `fa-${style}`;
        }
    }

    function getIconClasses(iconType, version) {
        const majorVer = parseInt(version.split('.')[0]);
        let prefix = majorVer <= 5 ? 'fas' : 'fa-solid';
        let name;
        switch (iconType) {
            case 'search':
                name = majorVer <= 5 ? 'fa-search' : 'fa-magnifying-glass';
                break;
            case 'arrow-up':
                name = 'fa-arrow-up';
                break;
            case 'arrow-left':
                name = 'fa-arrow-left';
                break;
            case 'arrow-right':
                name = 'fa-arrow-right';
                break;
            default:
                name = '';
        }
        return [prefix, name];
    }

    function fetchIcons(version){
        let url = `data/fontawesome-free-${version}-web/metadata/icons.json`;
        icons = [];
        fetch(url)
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
                                prefix: getStylePrefix(style, version), 
                                version: version,
                            });
                        });
                    }
                }
                // hiển thị tổng icon, tổng icon và page
                filteredIcons = icons;
                totalIcons = filteredIcons.length;
                totalPages = Math.ceil(filteredIcons.length / iconsPerPage);
                gettotalIcons(totalIcons);
                displayIconsForPage(currentPage);
                renderPagination();
                searchInput.dispatchEvent(new Event('input'));
            })
            .catch(error => console.error('Error loading icons:', error));
    }
    
    // Search event listener
    searchInput.addEventListener('input', () => {
        const query = searchInput.value.toLowerCase();
        filteredIcons = icons.filter(icon => 
            icon.name.toLowerCase().includes(query) || icon.label.toLowerCase().includes(query)
        );
        totalIcons = filteredIcons.length;
        gettotalIcons(totalIcons);
        totalPages = Math.ceil(filteredIcons.length / iconsPerPage); // Cập nhật tổng trang
        currentPage = 1; // Reset về trang 1
        displayIconsForPage(currentPage);
        renderPagination();
    });

    function displayIconsForPage(page) {
        iconGrid.innerHTML = '';  // Clear grid
        if (filteredIcons.length === 0) {
            iconGrid.style.display = 'block';
            const noResult = document.createElement('p');
            noResult.textContent = 'Không tìm thấy icon nào.';
            noResult.style.textAlign = 'center';
            noResult.style.fontSize = '1.2rem';
            noResult.style.color = 'rgb(43 48 54)';
            noResult.style.fontWeight = 'bold';
            noResult.style.margin = '20px 0';
            iconGrid.appendChild(noResult);
            return;  // Kết thúc hàm để tránh xử lý thêm
        }
        iconGrid.style.display = 'grid'
        const start = (page - 1) * iconsPerPage;
        const end = start + iconsPerPage;
        const pageIcons = filteredIcons.slice(start, end);

        pageIcons.forEach(icon => {
            const card = document.createElement('div');
            card.classList.add('icon-card');
            
            const iconElement = document.createElement('i');    
            const baseClass = icon.prefix;
            const iconNameClass = `fa-${icon.name}`; 
            iconElement.classList.add(baseClass, iconNameClass);

            const name = document.createElement('p');
            name.textContent = `${icon.name}`;

            const copied = document.createElement("p");
            copied.classList.add("copied");
            copied.textContent = "Đã copy code";

            card.appendChild(copied);

            card.addEventListener("click", () => {
                const majorVer = parseInt(icon.version.split('.')[0]);
                let htmlCode;
                if (majorVer <= 5) {
                    htmlCode = `<i class="${icon.prefix} fa-${icon.name}"></i>`;
                } else {
                    htmlCode = `<i class="${icon.prefix} fa-${icon.name}"></i>`;
                }
                navigator.clipboard.writeText(htmlCode)
                    .then(() => {
                        copied.classList.add('active'); 
                        setTimeout(() => {
                            copied.classList.remove('active'); 
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
        const prevClasses = getIconClasses('arrow-left', currentVersion);
        prevButton.innerHTML = `<i class="${prevClasses[0]} ${prevClasses[1]}"></i>`;
        prevButton.disabled = currentPage === 1;
        prevButton.addEventListener("click", ()=>{
            if (currentPage > 1) {  
                currentPage--;
                displayIconsForPage(currentPage);
                renderPagination();
            }
        });
        paginationContainer.appendChild(prevButton);

        const pageInfo = document.createElement('span');
        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
        pageInfo.style.cursor = "pointer";
        pageInfo.style.userSelect = "none"; 
        paginationContainer.appendChild(pageInfo);

        pageInfo.addEventListener("click", () => {
            inputPage(currentPage, pageInfo, paginationContainer, totalPages);
        });

        const nextButton = document.createElement("button");
        const nextClasses = getIconClasses('arrow-right', currentVersion);
        nextButton.innerHTML = `<i class="${nextClasses[0]} ${nextClasses[1]}"></i>`;
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
            renderPagination();  
        }

        inputPage.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                handleInputEnd(inputPage.value);
            }
        });

        inputPage.addEventListener("blur", () => {
            handleInputEnd(inputPage.value);
        });

        inputPage.addEventListener("input", () => {
            if (inputPage.value < 1) inputPage.value = 1;
            if (inputPage.value > totalPages) inputPage.value = totalPages;
        });
    }

    function gettotalIcons(totalIcons){
        const totalContainer = document.getElementById("total");
        totalContainer.innerText = totalIcons;
    }
});