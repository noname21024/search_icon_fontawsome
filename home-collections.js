document.addEventListener('DOMContentLoaded', () => {

    const MANIFEST_URL = 'data/collections-manifest.json';

    function injectCss(url) {
        if (document.querySelector(`link[href="${url}"]`)) {
            return; 
        }
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = url;
        document.head.appendChild(link);
        console.log(`Đã tải CSS: ${url}`);
    }

    function pickRandom(arr, n) {
        if (n > arr.length) return [...arr];
        let result = new Array(n),
            len = arr.length,
            taken = new Array(len);
        while (n--) {
            let x = Math.floor(Math.random() * len);
            result[n] = arr[x in taken ? taken[x] : x];
            taken[x] = --len in taken ? taken[len] : len;
        }
        return result;
    }

    function renderCollectionCard(collection) {
        const iconsHTML = (collection.previewIcons || []).map(iconClass => {
            return `<i class="${iconClass}"></i>`;
        }).join('');

        return `
        <a class="collections-card" href="${collection.href || 'render.html?collection=' + (collection.id || 'default')}">
            <div class="icons-container">
                ${iconsHTML}
            </div>
            <div class="icons-info">
                <h3>${collection.title} Collections</h3>
                <span>${collection.count || 0}</span>
            </div>
        </a>
        `;
    }

    const processors = {
        "icomoon-batch": async (collection) => {
            try {
                // THÊM LOG: Xác nhận collection object trước khi xử lý
                console.log(`Collection object cho ${collection.title}:`, collection);
                
                injectCss(collection.previewConfig.cssPath);
                const previewRes = await fetch(collection.previewConfig.dataPath);
                if (!previewRes.ok) throw new Error(`Lỗi tải preview ${collection.previewConfig.dataPath}`);
                const previewData = await previewRes.json();
                
                const preferences = previewData.preferences || {};
                const prefix = collection.classPrefix || preferences.classPrefix || 'icons-';
                console.log(`Prefix cho ${collection.title}: ${prefix} (collection.classPrefix: "${collection.classPrefix}", preferences.classPrefix: "${preferences.classPrefix}")`);  // Log chi tiết
                
                let previewIconsList = [];
                if (previewData.icons && Array.isArray(previewData.icons)) {
                    previewData.icons.forEach(icon => {
                        if (icon.properties && icon.properties.name) {
                            previewIconsList.push({ class: `${prefix}${icon.properties.name}`, name: icon.properties.name });
                        }
                    });
                } else {
                    console.warn(`Cấu trúc previewData không hợp lệ cho ${collection.title}:`, previewData);
                }
                
                const previewIconClasses = pickRandom(previewIconsList, 8).map(icon => icon.class);

                const countPromises = collection.countPaths.map(path =>
                    fetch(path)
                        .then(res => res.ok ? res.json() : Promise.reject(`Lỗi tải count ${path}`))
                        .then(data => {
                            return (data && data.icons && Array.isArray(data.icons)) ? data.icons.length : 0;
                        })
                        .catch(err => {
                            console.error(err);
                            return 0; 
                        })
                );
                
                const counts = await Promise.all(countPromises);
                const totalCount = counts.reduce((sum, current) => sum + current, 0);

                return {
                    ...collection,
                    count: totalCount,
                    previewIcons: previewIconClasses,
                };
            } catch (error) {
                console.error(`Lỗi xử lý icomoon-batch cho ${collection.title}:`, error);
                return {
                    ...collection,
                    count: 0,
                    previewIcons: []
                };
            }
        },

        "icomoon": async (collection) => {
            try {
                injectCss(collection.cssPath);
                const res = await fetch(collection.dataPath);
                if (!res.ok) throw new Error(`Lỗi tải ${collection.dataPath}`);
                const data = await res.json();

                const preferences = data.preferences || {};
                const prefix = collection.classPrefix || preferences.classPrefix || 'icons-';
                console.log(`Prefix cho ${collection.title}: ${prefix}`);  // Log debug
                
                let allIcons = [];
                if (data.icons && Array.isArray(data.icons)) {
                    data.icons.forEach(icon => {
                        if (icon.properties && icon.properties.name) {
                            allIcons.push({ class: `${prefix}${icon.properties.name}`, name: icon.properties.name });
                        }
                    });
                }

                return {
                    ...collection,
                    count: allIcons.length,
                    previewIcons: pickRandom(allIcons, 8).map(icon => icon.class),
                    id: collection.id
                };
            } catch (error) {
                console.error(`Lỗi xử lý icomoon cho ${collection.title}:`, error);
                return {
                    ...collection,
                    count: 0,
                    previewIcons: []
                };
            }
        },

        "fa-optimized": async (collection) => {
            try {
                injectCss(collection.cssPath);
                const res = await fetch(collection.dataPath);
                if (!res.ok) throw new Error(`Lỗi tải ${collection.dataPath}`);
                const data = await res.json();

                let allIcons = [];
                const getStylePrefix = (style) => `fa-${style}`;
                for (const [name, iconData] of Object.entries(data)) {
                    if (iconData.f && Array.isArray(iconData.f)) {
                        iconData.f.forEach(style => {
                            allIcons.push({ class: `${getStylePrefix(style, '7.1.0')} fa-${name}`, name: name });
                        });
                    }
                }
                
                return {
                    ...collection,
                    count: allIcons.length,
                    previewIcons: pickRandom(allIcons, 8).map(icon => icon.class),
                    id: collection.id
                };
            } catch (error) {
                console.error(`Lỗi xử lý fa-optimized cho ${collection.title}:`, error);
                return {
                    ...collection,
                    count: 0,
                    previewIcons: []
                };
            }
        }
    };

    async function initializeCollections() {
        const gridContainer = document.querySelector('.collections-grid');
        if (!gridContainer) {
            console.error('Lỗi: Không tìm thấy container ".collections-grid"');
            return;
        }
        gridContainer.innerHTML = ''; 

        try {
            const manifestResponse = await fetch(MANIFEST_URL);
            if (!manifestResponse.ok) throw new Error(`Không tìm thấy ${MANIFEST_URL}`);
            const collectionsToLoad = await manifestResponse.json();

            // THÊM LOG: Xác nhận toàn bộ manifest được tải
            console.log('Collections từ manifest:', collectionsToLoad);

            const fetchPromises = collectionsToLoad.map(collection => {
                const processor = processors[collection.processorType];
                if (!processor) {
                    console.warn(`Không tìm thấy processor: ${collection.processorType} cho ${collection.title}`);
                    return Promise.resolve({
                        ...collection,
                        count: 0,
                        previewIcons: []
                    });
                }
                return processor(collection); 
            });

            const fullyProcessedCollections = await Promise.all(fetchPromises);

            fullyProcessedCollections.forEach(collection => {
                gridContainer.innerHTML += renderCollectionCard(collection);
            });

        } catch (error) {
            console.error('Lỗi nghiêm trọng khi tải collections:', error);
            gridContainer.innerHTML = `<p style="color: red; padding: 1rem;">${error.message}</p>`;
        }
    }

    initializeCollections();
});