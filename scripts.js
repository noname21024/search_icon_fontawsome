const elements = {};
const state = {
    icons: [],
    filteredIcons: [],
    currentPage: 1,
    iconsPerPage: 100,
    totalPages: 0,
    currentConfig: null,
    allCollections: null,
    db: {} 
};
const LAZY_FAMILIES = ['lawnicons', 'simpleicons'];

document.addEventListener('DOMContentLoaded', initializeApp);

async function initializeApp() {
    cacheElements();
    await loadCollectionsDatabase();
    await setupCollectionFromURL();
    setupEventListeners();
}

function cacheElements() {
    const ids = ['searchInput', 'iconGrid', 'fontawesome_version', 'copyCDN', 'total', 'pagination'];
    ids.forEach(id => elements[id] = document.getElementById(id));
    elements.copiedCDN = document.querySelector('.copied-cnd');
    elements.versionContainer = document.querySelector('.version-fontawesome_container');
    elements.pageTitle = document.querySelector('.header h1');
    elements.downloadBtn = document.querySelector('.download-btn');
}

async function loadCollectionsDatabase() {
    try {
        const res = await fetch('data/collections-database.json');
        if (!res.ok) throw new Error('Không thể tải collections-database.json');
        state.allCollections = await res.json();
    } catch (err) {
        showError(err.message);
    }
}

async function setupCollectionFromURL() {
    const params = new URLSearchParams(location.search);
    let id = params.get('collection') || 'fontawesome-7.1.0';

    if (!state.allCollections[id]) {
        id = Object.keys(state.allCollections)[0];
        updateURL(id);
    }

    state.currentConfig = { ...state.allCollections[id], id };
    setupUI(state.currentConfig);

    // Kiểm tra nếu family trong LAZY_FAMILIES hoặc config có metadata (cho lazy loading)
    if (LAZY_FAMILIES.includes(state.currentConfig.family) || state.currentConfig.metadata) {
        await initLazyLoading(state.currentConfig);  // Sử dụng hàm chung cho lazy
    } else {
        await loadCollectionData(state.currentConfig);
    }
}

function updateURL(collectionId) {
    const url = new URL(location);
    url.searchParams.set('collection', collectionId);
    history.replaceState(null, '', url);
}

function setupUI(config) {
    elements.pageTitle.textContent = config.title;
    document.title = `${config.title} - Copy Icons`;
    document.getElementById('fontawesomeCss').href = config.css;
    elements.downloadBtn.href = config.download;
    elements.downloadBtn.download = config.download.split('/').pop();

    if (config.family === 'fontawesome') {
        elements.versionContainer.style.display = 'flex';
        populateFontAwesomeVersions(config.id);
    } else {
        elements.versionContainer.style.display = 'none';
    }

    updateSearchIcon(config);
}

function populateFontAwesomeVersions(currentId) {
    const faCollections = Object.entries(state.allCollections)
        .filter(([_, c]) => c.family === 'fontawesome')
        .map(([id, c]) => ({ id, title: c.title, version: c.version }))
        .sort((a, b) => b.version.localeCompare(a.version, undefined, { numeric: true }));

    elements.fontawesome_version.innerHTML = '';
    faCollections.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v.id;
        opt.textContent = v.version;  // Chỉ dùng version ngắn
        elements.fontawesome_version.appendChild(opt);
    });
    elements.fontawesome_version.value = currentId;
}

async function openDB(collectionId) {
    const dbName = `${collectionId.replace(/[^a-z0-9]/gi, '_')}_icons_db`;
    if (state.db[dbName]) return state.db[dbName];

    return new Promise((resolve, reject) => {
        const req = indexedDB.open(dbName, 1);
        req.onupgradeneeded = e => {
            const db = e.target.result;
            ['chunks', 'metadata'].forEach(store => {
                if (!db.objectStoreNames.contains(store)) {
                    db.createObjectStore(store, { keyPath: store === 'chunks' ? 'chunkIndex' : 'id' });
                }
            });
        };
        req.onsuccess = e => {
            state.db[dbName] = e.target.result;
            resolve(state.db[dbName]);
        };
        req.onerror = () => reject(req.error);
    });
}

async function dbPut(storeName, data, collectionId) {
    const db = await openDB(collectionId);
    return new Promise(resolve => {
        const tx = db.transaction(storeName, 'readwrite');
        tx.objectStore(storeName).put(data);
        tx.oncomplete = resolve;
    });
}

async function dbGet(storeName, key, collectionId) {
    const db = await openDB(collectionId);
    return new Promise(resolve => {
        const tx = db.transaction(storeName, 'readonly');
        const req = tx.objectStore(storeName).get(key);
        req.onsuccess = () => resolve(req.result);
    });
}

let lazyMetadata = null;
let chunkSize = 0;
let numberOfChunks = 0;

async function initLazyLoading(config) {
    try {
        await openDB(config.id);
        let cachedMeta = await dbGet('metadata', 'metadata', config.id);

        if (cachedMeta && cachedMeta.data) {
            lazyMetadata = cachedMeta.data;
            console.log(`✅ Metadata từ IndexedDB cho ${config.title}`);
        } else {
            const res = await fetch(config.metadata);
            if (!res.ok) throw new Error('Không tải được metadata');
            lazyMetadata = await res.json();
            await dbPut('metadata', { id: 'metadata', data: lazyMetadata }, config.id);
            console.log(`✅ Đã lưu metadata cho ${config.title}`);
        }

        chunkSize = lazyMetadata.chunk_size || 500;
        numberOfChunks = lazyMetadata.chunks?.length || Math.ceil(lazyMetadata.total_icons / chunkSize);

        updateTotal(lazyMetadata.total_icons);
        state.totalPages = Math.ceil(lazyMetadata.total_icons / state.iconsPerPage);
        state.currentPage = 1;
        state.filteredIcons = []; // Không load full ban đầu
        await loadLazyPage(1, config);  // Load trang đầu với config
        renderPagination();
    } catch (err) {
        showError(err.message);
    }
}

async function loadLazyPage(page, config) {
    try {
        const start = (page - 1) * state.iconsPerPage;
        const end = Math.min(start + state.iconsPerPage, lazyMetadata.total_icons);
        const firstChunk = Math.floor(start / chunkSize);
        const lastChunk = Math.floor((end - 1) / chunkSize);
        let allChunkIcons = [];

        for (let ci = firstChunk; ci <= lastChunk; ci++) {
            let result = await dbGet('chunks', ci, config.id);
            let chunk = result ? result.icons : null;

            if (!chunk || !Array.isArray(chunk)) {
                const chunkPath = config.chunkPattern.replace('{index}', ci);
                const res = await fetch(chunkPath);
                if (!res.ok) {
                    console.warn(`Không tải được chunk ${ci} cho ${config.title}`);
                    continue;
                }
                const rawData = await res.json();

                if (!rawData || !Array.isArray(rawData.icons)) {
                    console.error(`Chunk ${ci} có cấu trúc sai cho ${config.title}:`, rawData);
                    continue;
                }

                const prefix = config.classPrefix || 'icon-';
                chunk = rawData.icons.map(icon => ({
                    name: icon.properties?.name || icon.name || 'unknown',
                    label: icon.properties?.name || icon.name || 'unknown',
                    terms: icon.icon?.tags || (icon.tags || []),
                    tags: icon.tags || [],
                    description: icon.description || '',
                    category: icon.category || '',
                    htmlCode: `<i class="${prefix}${icon.properties?.name || icon.name}"></i>`
                }));

                await dbPut('chunks', { chunkIndex: ci, icons: chunk }, config.id);
                console.log(`✅ Parsed chunk ${ci} cho ${config.title}: ${chunk.length} icons`);
            }

            if (Array.isArray(chunk)) {
                allChunkIcons = allChunkIcons.concat(chunk);
            } else {
                console.warn(`Chunk ${ci} không phải mảng sau parse cho ${config.title}:`, chunk);
            }
        }

        const globalStartInChunks = start - firstChunk * chunkSize;
        const neededCount = end - start;
        const pageIcons = allChunkIcons.slice(Math.max(0, globalStartInChunks), globalStartInChunks + neededCount);

        displayIcons(pageIcons);
    } catch (err) {
        console.error('Lỗi loadLazyPage:', err);
        showError(`Lỗi tải trang cho ${config.title}: ${err.message}`);
    }
}

async function loadCollectionData(config) {
    const parser = {
        'fa-optimized': parseFontAwesome,
        'icomoon': parseIcoMoon,
        'icomoon-batch': parseIcoMoonBatch
    }[config.processorType];

    if (!parser) throw new Error(`Processor không hỗ trợ: ${config.processorType}`);

    // SỬA: Kiểm tra config.json tồn tại trước khi map
    if (!config.json || !Array.isArray(config.json)) {
        throw new Error(`Config.json không hợp lệ cho ${config.title}`);
    }

    const data = await Promise.all(config.json.map(path => fetch(path).then(r => r.json())));
    state.icons = state.filteredIcons = parser(data, config);

    updateTotal(state.icons.length);
    state.totalPages = Math.ceil(state.icons.length / state.iconsPerPage);
    state.currentPage = 1;

    // Slice ngay từ đầu để render chỉ 100 icons
    const start = (state.currentPage - 1) * state.iconsPerPage;
    const end = start + state.iconsPerPage;
    displayIcons(state.filteredIcons.slice(start, end));

    renderPagination();
}

function parseFontAwesome([data], config) {
    const getPrefix = style => config.fa_style === 'old' 
        ? { solid: 'fas', regular: 'far', brands: 'fab' }[style] || 'fas' 
        : `fa-${style}`;

    const icons = [];
    for (const [name, info] of Object.entries(data)) {
        (info.f || []).forEach(style => {
            icons.push({
                name,
                label: info.l,
                terms: info.t || [],
                htmlCode: `<i class="${getPrefix(style)} fa-${name}"></i>`
            });
        });
    }
    return icons;
}

function parseIcoMoon([data], config) {
    const prefix = config.classPrefix || 'icon-';
    return (data.icons || []).map(icon => ({
        name: icon.properties?.name || 'unknown',
        label: icon.properties?.name || 'unknown',
        terms: icon.icon?.tags || [],
        tags: icon.tags || [],
        description: icon.description || '',
        category: icon.category || '',
        htmlCode: `<i class="${prefix}${icon.properties?.name || 'unknown'}"></i>`
    }));
}

function parseIcoMoonBatch(dataArray, config) {
    const prefix = config.classPrefix || 'icon-';
    const icons = [];
    dataArray.forEach(data => {
        if (data.icons) {
            data.icons.forEach(icon => {
                const iconObj = icon.icon || {};
                const props = icon.properties || {};
                icons.push({
                    name: props.name || 'unknown',
                    label: props.name || 'unknown',
                    terms: iconObj.tags || [],
                    tags: [...(iconObj.tags || []), ...(props.tags || [])],
                    description: props.description || '',
                    category: props.category || '',
                    htmlCode: `<i class="${prefix}${props.name || 'unknown'}"></i>`
                });
            });
        }
    });
    return icons;
}

// Thêm hàm loading indicator
function showLoading(show = true) {
    const grid = elements.iconGrid;
    if (show) {
        grid.innerHTML = '<p style="text-align:center; color:#666;">Đang tìm kiếm...</p>';
    }
}

async function handleSearch() {
    showLoading(true);
    const query = elements.searchInput.value.toLowerCase();

    if (LAZY_FAMILIES.includes(state.currentConfig.family) || state.currentConfig.metadata) {
        if (query === '') {
            state.filteredIcons = [];
            updateTotal(lazyMetadata.total_icons);
            state.totalPages = Math.ceil(lazyMetadata.total_icons / state.iconsPerPage);
            state.currentPage = 1;
            await loadLazyPage(state.currentPage, state.currentConfig);
        } else {
            if (state.icons.length === 0) {
                console.log('🔄 Đang load full icons cho search...');
                let allIcons = [];
                for (let ci = 0; ci < numberOfChunks; ci++) {
                    let result = await dbGet('chunks', ci, state.currentConfig.id);
                    let chunk = result ? result.icons : null;

                    if (!chunk || !Array.isArray(chunk)) {
                        const chunkPath = state.currentConfig.chunkPattern.replace('{index}', ci);
                        const res = await fetch(chunkPath);
                        if (!res.ok) continue;
                        const rawData = await res.json();
                        if (!Array.isArray(rawData.icons)) continue;

                        const prefix = state.currentConfig.classPrefix || 'icon-';
                        chunk = rawData.icons.map(icon => ({
                            name: icon.properties?.name || icon.name || 'unknown',
                            label: icon.properties?.name || icon.name || 'unknown',
                            terms: icon.icon?.tags || (icon.tags || []),
                            tags: icon.tags || [],
                            description: icon.description || '',
                            category: icon.category || '',
                            htmlCode: `<i class="${prefix}${icon.properties?.name || icon.name}"></i>`
                        }));
                        await dbPut('chunks', { chunkIndex: ci, icons: chunk }, state.currentConfig.id);
                    }

                    if (Array.isArray(chunk)) {
                        allIcons = allIcons.concat(chunk);
                    }
                }
                state.icons = allIcons;
                console.log(`✅ Loaded full ${state.icons.length} icons cho search`);
            }

            state.filteredIcons = state.icons.filter(icon =>
                icon.name.toLowerCase().includes(query) ||
                (icon.label || '').toLowerCase().includes(query) ||
                (icon.terms || []).some(t => t.toLowerCase().includes(query)) ||
                (icon.tags || []).some(t => t.toLowerCase().includes(query)) ||
                (icon.description || '').toLowerCase().includes(query) ||
                (icon.category || '').toLowerCase().includes(query)
            );
            updateTotal(state.filteredIcons.length);
            state.totalPages = Math.ceil(state.filteredIcons.length / state.iconsPerPage);
            state.currentPage = 1;
            displayIcons(state.filteredIcons);
        }
        renderPagination();
    } else {
        state.filteredIcons = state.icons.filter(icon =>
            icon.name.toLowerCase().includes(query) ||
            (icon.label || '').toLowerCase().includes(query) ||
            (icon.terms || []).some(t => t.toLowerCase().includes(query))
        );

        updateTotal(state.filteredIcons.length);
        state.totalPages = Math.ceil(state.filteredIcons.length / state.iconsPerPage);
        state.currentPage = 1;
        displayIcons(state.filteredIcons);
        renderPagination();
    }

    showLoading(false);
}

function displayIcons(iconsToShow) {
    const grid = elements.iconGrid;
    grid.innerHTML = '';

    if (!Array.isArray(iconsToShow) || iconsToShow.length === 0) {
        grid.innerHTML = '<p style="text-align:center; color:#2b3036; font-weight:bold;">Không tìm thấy icon nào.</p>';
        return;
    }

    const frag = document.createDocumentFragment();
    iconsToShow.forEach(icon => {
        const card = document.createElement('div');
        card.className = 'icon-card';
        card.innerHTML = `
            <p class="copied">Đã copy code</p>
            ${icon.htmlCode}
            <p>${icon.name}</p>
        `;
        card.onclick = () => copyToClipboard(icon.htmlCode, card.querySelector('.copied'));
        frag.appendChild(card);
    });
    grid.appendChild(frag);
}

function copyToClipboard(text, feedbackEl) {
    navigator.clipboard.writeText(text).then(() => {
        feedbackEl.classList.add('active');
        setTimeout(() => feedbackEl.classList.remove('active'), 1000);
    }).catch(err => console.error('Copy failed:', err));
}

function updateTotal(count) {
    elements.total.textContent = count;
}

function renderPagination() {
    const container = elements.pagination;
    container.innerHTML = '';

    if (state.totalPages <= 1) return;

    const prev = createButton('prev', async () => {
        if (state.currentPage > 1) {
            state.currentPage--;
            await refreshPage();
        }
    }, state.currentPage === 1);

    const info = document.createElement('span');
    info.textContent = `Page ${state.currentPage} of ${state.totalPages}`;
    info.style.cursor = 'pointer';
    info.onclick = () => showPageInput(info);

    const next = createButton('next', async () => {
        if (state.currentPage < state.totalPages) {
            state.currentPage++;
            await refreshPage();
        }
    }, state.currentPage === state.totalPages);

    container.append(prev, info, next);
}

function createButton(type, onclick, disabled) {
    const btn = document.createElement('button');
    btn.disabled = disabled;
    btn.innerHTML = type === 'prev'
        ? `<svg width="25" height="23" viewBox="0 0 24 24" fill="none"><path d="M6 12H18M6 12L11 7M6 12L11 17" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`
        : `<svg width="25" height="23" viewBox="0 0 24 24" fill="none"><path d="M6 12H18M18 12L13 7M18 12L13 17" stroke="#000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
    btn.onclick = onclick;
    return btn;
}

async function refreshPage() {
    if ((LAZY_FAMILIES.includes(state.currentConfig.family) || state.currentConfig.metadata) && elements.searchInput.value === '') {
        await loadLazyPage(state.currentPage, state.currentConfig);
    } else {
        const start = (state.currentPage - 1) * state.iconsPerPage;
        const end = start + state.iconsPerPage;
        const pageIcons = state.filteredIcons.slice(start, end);
        displayIcons(pageIcons);
    }
    renderPagination();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function showPageInput(infoEl) {
    infoEl.style.display = 'none';
    const input = document.createElement('input');
    input.type = 'number';
    input.min = 1;
    input.max = state.totalPages;
    input.value = state.currentPage;
    input.className = 'pagination-input';
    elements.pagination.insertBefore(input, infoEl.nextSibling);
    input.focus();
    input.select();

    const apply = async () => {
        let page = parseInt(input.value) || state.currentPage;
        page = Math.max(1, Math.min(state.totalPages, page));
        if (page !== state.currentPage) {
            state.currentPage = page;
            await refreshPage();
        }
        input.remove();
        renderPagination();
    };

    input.onkeydown = e => e.key === 'Enter' && apply();
    input.onblur = apply;
}

function setupEventListeners() {
    // Debounce search input
    let searchTimeout;
    elements.searchInput.oninput = () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            handleSearch();
        }, 300); // Chờ 300ms sau khi ngừng gõ
    };

    elements.copyCDN.onclick = () => {
        navigator.clipboard.writeText(state.currentConfig.cdn);
        elements.copiedCDN.classList.add('active');
        setTimeout(() => elements.copiedCDN.classList.remove('active'), 1500);
    };
    elements.fontawesome_version.onchange = e => {
        updateURL(e.target.value);
        location.reload();
    };
}

function updateSearchIcon(config) {
    const icon = document.querySelector('.search-container i');
    if (!icon) return;

    let classes = [];
    if (config.family === 'fontawesome') {
        classes = config.fa_style === 'old'
            ? ['fas', 'fa-search']
            : ['fa-solid', 'fa-magnifying-glass'];
    } else {
        classes = [config.classPrefix + 'search'];
    }
    icon.className = '';
    icon.classList.add(...classes);
}

function showError(msg) {
    elements.iconGrid.innerHTML = `<p style="color:red; text-align:center;">${msg}</p>`;
}