document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const iconGrid = document.getElementById('iconGrid');
    let icons = [];
    fetch('metadata/icons.json')  // Adjust path to your local icons.json
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
            displayIcons(icons);  
        })
        .catch(error => console.error('Error loading icons:', error));

    // Search event listener
    searchInput.addEventListener('input', () => {
        const query = searchInput.value.toLowerCase();
        const filteredIcons = icons.filter(icon => 
            icon.name.toLowerCase().includes(query) || icon.label.toLowerCase().includes(query)
        );
        displayIcons(filteredIcons);
    });

    // Function to display icons in grid
    function displayIcons(iconList) {
        iconGrid.innerHTML = '';  // Clear grid
        iconList.forEach(icon => {
            const card = document.createElement('div');
            card.classList.add('icon-card');

            const iconElement = document.createElement('i');
            iconElement.classList.add(icon.prefix, `${icon.prefix.split('-')[0]}-${icon.name}`);  

            const label = document.createElement('p');
            label.textContent = icon.label;

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
            // card.appendChild(label);
            card.appendChild(name);
            iconGrid.appendChild(card);
        });
    }
});