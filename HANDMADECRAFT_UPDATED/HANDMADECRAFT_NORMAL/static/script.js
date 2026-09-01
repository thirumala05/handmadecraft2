"use strict";

let products = [];
let cartItems = [];
let currentUser = window.INITIAL_USER || null;
let activeCategory = "All";
let toastTimer;

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const productContainer = $("#productContainer");
const categoryRow = $("#categoryRow");
const searchInput = $("#searchInput");
const sortFilter = $("#sortFilter");
const catalogSearch = $("#catalogSearch");
const catalogCategory = $("#catalogCategory");
const catalogSort = $("#catalogSort");
const catalogCount = $("#catalogCount");
const cartCount = $("#cartCount");
const cartContainer = $("#cartContainer");
const cartTotal = $("#cartTotal");
const cartDrawer = $("#cartDrawer");
const overlay = $("#overlay");
const authModal = $("#authModal");
const productModal = $("#productModal");
const checkoutModal = $("#checkoutModal");
const authButton = $("#authButton");
const authButtonText = $("#authButtonText");

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "'": "&#39;",
        '"': "&quot;",
    }[char]));
}

function money(value) {
    return `₹${Number(value || 0).toLocaleString("en-IN")}`;
}

function imageUrl(image) {
    if (!image) return `${window.STATIC_IMAGE_BASE}girija.jpeg`;
    if (/^https?:\/\//i.test(image)) return image;
    return `${window.STATIC_IMAGE_BASE}${encodeURIComponent(image)}`;
}

async function api(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {}),
        },
    });

    let data = {};
    try {
        data = await response.json();
    } catch (_) {
        data = { success: false, message: "The server returned an invalid response." };
    }

    if (!response.ok) {
        const error = new Error(data.message || "Something went wrong.");
        error.status = response.status;
        error.data = data;
        throw error;
    }
    return data;
}

function showToast(message) {
    const toast = $("#toast");
    toast.textContent = message;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 2800);
}

function updateAuthUI() {
    if (currentUser) {
        const firstName = currentUser.name.trim().split(/\s+/)[0];
        authButtonText.textContent = `${firstName} · Sign out`;
        authButton.dataset.mode = "logout";
    } else {
        authButtonText.textContent = "Sign in";
        authButton.dataset.mode = "login";
        cartItems = [];
        renderCart();
    }
}

function openModal(modal) {
    closeCart();
    modal.classList.add("active");
    document.body.classList.add("modal-open");
}

function closeModal(modal) {
    modal?.classList.remove("active");
    if (!$$(".modal.active").length && !cartDrawer.classList.contains("active")) {
        document.body.classList.remove("modal-open");
    }
}

function setAuthMode(mode) {
    $$(".auth-tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.authMode === mode));
    $("#loginForm").classList.toggle("hidden", mode !== "login");
    $("#registerForm").classList.toggle("hidden", mode !== "register");
    $("#authMessage").textContent = "";
}

function openAuth(mode = "login") {
    setAuthMode(mode);
    openModal(authModal);
}

async function loadProducts() {
    productContainer.innerHTML = '<div class="loading-state">Loading handmade pieces…</div>';
    try {
        const data = await api("/api/catalog", { method: "GET", headers: {} });
        products = data.products || [];
        renderCategories(data.categories || []);
        renderCatalogCategories(data.categories || []);
        renderProducts();
        updateCatalogCount();
    } catch (error) {
        productContainer.innerHTML = `<div class="empty-state"><strong>We couldn't load the catalog.</strong><br>${escapeHtml(error.message)}</div>`;
    }
}

function renderCatalogCategories(categories) {
    if (!catalogCategory) return;
    catalogCategory.innerHTML = '<option value="All">All categories</option>' +
        categories.map((category) => `<option value="${escapeHtml(category)}">${escapeHtml(category)}</option>`).join("");
}

function updateCatalogCount() {
    if (catalogCount) catalogCount.textContent = products.length.toLocaleString("en-IN");
}

function renderCategories() {
    const categories = ["All", ...new Set(products.map((product) => product.category).filter(Boolean))];
    categoryRow.innerHTML = categories.map((category) => `
        <button type="button" class="category-pill ${activeCategory === category ? "active" : ""}" data-category="${escapeHtml(category)}">
            ${escapeHtml(category)}
        </button>
    `).join("");
}

function filteredProducts() {
    const query = (catalogSearch?.value || searchInput.value).trim().toLowerCase();
    const selectedCategory = catalogCategory?.value || activeCategory;
    let list = products.filter((product) => {
        const haystack = [
            product.name, product.category, product.description,
            product.artisan, product.material, product.sku
        ].map((value) => String(value || "").toLowerCase());
        const matchesSearch = !query || haystack.some((value) => value.includes(query));
        const matchesCategory = selectedCategory === "All" || product.category === selectedCategory;
        return matchesSearch && matchesCategory;
    });

    const mode = catalogSort?.value || sortFilter.value;
    list = [...list];
    if (mode === "low") list.sort((a, b) => a.price - b.price);
    if (mode === "high") list.sort((a, b) => b.price - a.price);
    if (mode === "rating") list.sort((a, b) => b.rating - a.rating);
    if (mode === "discount") list.sort((a, b) => b.discount - a.discount);
    if (mode === "featured") list.sort((a, b) => Number(b.featured) - Number(a.featured));
    return list;
}

function renderProducts() {
    const list = filteredProducts();
    if (!list.length) {
        productContainer.innerHTML = '<div class="empty-state"><strong>No pieces found.</strong><br>Try a different search or category.</div>';
        return;
    }

    productContainer.innerHTML = list.map((product) => {
        const soldOut = Number(product.stock) <= 0;
        return `
            <article class="product-card">
                <button type="button" class="product-image-box view-product" data-id="${product.id}" aria-label="View ${escapeHtml(product.name)}" style="border:0;padding:0;width:100%;text-align:left">
                    ${product.badge ? `<span class="product-badge">${escapeHtml(product.badge)}</span>` : ""}
                    <img src="${imageUrl(product.image)}" alt="${escapeHtml(product.name)}" loading="lazy">
                </button>
                <div class="product-details">
                    <div class="product-meta"><span>${escapeHtml(product.category)}</span><span>${Number(product.rating).toFixed(1)} ★</span></div>
                    <h3>${escapeHtml(product.name)}</h3>
                    <div class="price-row">
                        <span class="current-price">${money(product.price)}</span>
                        ${product.oldPrice ? `<span class="old-price">${money(product.oldPrice)}</span>` : ""}
                        ${product.discount ? `<span class="discount">${product.discount}% off</span>` : ""}
                    </div>
                    <div class="stock-row">
                        <span class="stock-badge ${soldOut ? "out" : "in"}">${soldOut ? "Out of stock" : `In stock · ${product.stock}`}</span>
                        ${product.badge ? `<span class="catalog-badge">${escapeHtml(product.badge)}</span>` : ""}
                    </div>
                    <div class="product-actions">
                        <button type="button" class="add-btn" data-add-id="${product.id}" ${soldOut ? "disabled" : ""}>${soldOut ? "Sold out" : "Add to cart"}</button>
                        <button type="button" class="view-btn view-product" data-id="${product.id}" aria-label="View details">→</button>
                    </div>
                </div>
            </article>
        `;
    }).join("");
}

function openProduct(productId) {
    const product = products.find((item) => item.id === Number(productId));
    if (!product) return;

    const soldOut = Number(product.stock) <= 0;
    $("#productModalContent").innerHTML = `
        <button class="icon-btn modal-close" type="button" data-close-modal aria-label="Close">×</button>
        <div class="product-modal-grid">
            <img src="${imageUrl(product.image)}" alt="${escapeHtml(product.name)}">
            <div class="product-modal-info">
                <span class="eyebrow">${escapeHtml(product.category)}</span>
                <h2>${escapeHtml(product.name)}</h2>
                <div class="modal-rating">${Number(product.rating).toFixed(1)} ★ · ${Number(product.reviews || 0).toLocaleString("en-IN")} reviews</div>
                <div class="price-row" style="margin-top:18px">
                    <span class="current-price" style="font-size:24px">${money(product.price)}</span>
                    ${product.oldPrice ? `<span class="old-price">${money(product.oldPrice)}</span>` : ""}
                </div>
                <div class="modal-status-row">
                    <span class="modal-stock ${soldOut ? "out" : "in"}">${soldOut ? "Currently sold out" : `In stock · ${product.stock} available`}</span>
                    ${product.badge ? `<span class="catalog-badge">${escapeHtml(product.badge)}</span>` : ""}
                </div>
                <p>${escapeHtml(product.description)}</p>
                <div class="catalog-details">
                    <div><span>SKU</span><strong>${escapeHtml(product.sku || "—")}</strong></div>
                    <div><span>Artisan</span><strong>${escapeHtml(product.artisan || "HandmadeCraft Studio")}</strong></div>
                    <div><span>Material</span><strong>${escapeHtml(product.material || "Handcrafted")}</strong></div>
                    <div><span>Dispatch</span><strong>${Number(product.deliveryDays || 5)} days</strong></div>
                </div>
                <button class="primary-btn full-width" type="button" data-add-id="${product.id}" ${soldOut ? "disabled" : ""}>${soldOut ? "Sold out" : "Add to cart"}</button>
            </div>
        </div>
    `;
    openModal(productModal);
}

async function loadCart() {
    if (!currentUser) {
        cartItems = [];
        renderCart();
        return;
    }
    try {
        const data = await api("/api/cart", { method: "GET", headers: {} });
        cartItems = data.items || [];
        renderCart();
    } catch (error) {
        if (error.status === 401) {
            currentUser = null;
            updateAuthUI();
        } else {
            showToast(error.message);
        }
    }
}

function renderCart() {
    const count = cartItems.reduce((sum, item) => sum + Number(item.quantity || 0), 0);
    const total = cartItems.reduce((sum, item) => sum + Number(item.price) * Number(item.quantity), 0);
    cartCount.textContent = count;
    cartTotal.textContent = money(total);

    if (!currentUser) {
        cartContainer.innerHTML = '<div class="empty-cart"><strong>Sign in to use your bag.</strong><span>Your cart is stored with your account.</span></div>';
        return;
    }
    if (!cartItems.length) {
        cartContainer.innerHTML = '<div class="empty-cart"><strong>Your bag is empty.</strong><span>Add a handmade piece you love.</span></div>';
        return;
    }

    cartContainer.innerHTML = cartItems.map((item) => `
        <div class="cart-item">
            <img class="cart-thumb" src="${imageUrl(item.image)}" alt="${escapeHtml(item.name)}">
            <div>
                <h3>${escapeHtml(item.name)}</h3>
                <p>${money(item.price)}</p>
                <div class="quantity-control">
                    <button type="button" data-qty-id="${item.id}" data-quantity="${item.quantity - 1}" aria-label="Decrease quantity">−</button>
                    <span>${item.quantity}</span>
                    <button type="button" data-qty-id="${item.id}" data-quantity="${item.quantity + 1}" aria-label="Increase quantity" ${item.quantity >= item.stock ? "disabled" : ""}>+</button>
                </div>
            </div>
            <button type="button" class="remove-btn" data-remove-id="${item.id}" aria-label="Remove ${escapeHtml(item.name)}">×</button>
        </div>
    `).join("");
}

async function addToCart(productId) {
    if (!currentUser) {
        showToast("Sign in to add items to your bag.");
        openAuth("login");
        return;
    }
    try {
        await api("/api/cart", {
            method: "POST",
            body: JSON.stringify({ product_id: Number(productId), quantity: 1 }),
        });
        await loadCart();
        closeModal(productModal);
        showToast("Added to your bag.");
    } catch (error) {
        showToast(error.message);
    }
}

async function updateCartQuantity(productId, quantity) {
    try {
        await api(`/api/cart/${productId}`, {
            method: "PATCH",
            body: JSON.stringify({ quantity: Number(quantity) }),
        });
        await loadCart();
    } catch (error) {
        showToast(error.message);
    }
}

async function removeCartItem(productId) {
    try {
        await api(`/api/cart/${productId}`, { method: "DELETE" });
        await loadCart();
        showToast("Removed from your bag.");
    } catch (error) {
        showToast(error.message);
    }
}

function openCart() {
    if (!currentUser) {
        showToast("Sign in to view your bag.");
        openAuth("login");
        return;
    }
    cartDrawer.classList.add("active");
    cartDrawer.setAttribute("aria-hidden", "false");
    overlay.classList.add("active");
    document.body.classList.add("modal-open");
    loadCart();
}

function closeCart() {
    cartDrawer.classList.remove("active");
    cartDrawer.setAttribute("aria-hidden", "true");
    overlay.classList.remove("active");
    if (!$$(".modal.active").length) document.body.classList.remove("modal-open");
}

async function handleLogin(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const message = $("#authMessage");
    message.className = "form-message";
    message.textContent = "Signing in…";
    try {
        const data = await api("/api/login", {
            method: "POST",
            body: JSON.stringify({ email: form.get("email"), password: form.get("password") }),
        });
        currentUser = data.user;
        updateAuthUI();
        await loadCart();
        message.classList.add("success");
        message.textContent = "Signed in successfully.";
        setTimeout(() => closeModal(authModal), 350);
        showToast(`Welcome back, ${currentUser.name.split(" ")[0]}.`);
    } catch (error) {
        message.textContent = error.message;
    }
}

async function handleRegister(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const message = $("#authMessage");
    message.className = "form-message";
    message.textContent = "Creating your account…";
    try {
        const data = await api("/api/register", {
            method: "POST",
            body: JSON.stringify({
                name: form.get("name"),
                email: form.get("email"),
                password: form.get("password"),
            }),
        });
        currentUser = data.user;
        updateAuthUI();
        await loadCart();
        message.classList.add("success");
        message.textContent = "Account created.";
        setTimeout(() => closeModal(authModal), 350);
        showToast(`Welcome, ${currentUser.name.split(" ")[0]}.`);
    } catch (error) {
        message.textContent = error.message;
    }
}

async function logout() {
    try {
        await api("/api/logout", { method: "POST", body: "{}" });
    } catch (_) {
        // Clear local UI even if the session has already expired.
    }
    currentUser = null;
    cartItems = [];
    updateAuthUI();
    closeCart();
    showToast("Signed out.");
}

function beginCheckout() {
    if (!currentUser) {
        openAuth("login");
        return;
    }
    if (!cartItems.length) {
        showToast("Your bag is empty.");
        return;
    }
    $("#checkoutMessage").textContent = "";
    openModal(checkoutModal);
}

async function handleCheckout(event) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const message = $("#checkoutMessage");
    const button = $("button[type='submit']", event.currentTarget);
    button.disabled = true;
    message.className = "form-message";
    message.textContent = "Placing your order…";
    try {
        const data = await api("/api/orders", {
            method: "POST",
            body: JSON.stringify({ phone: form.get("phone"), address: form.get("address") }),
        });
        message.classList.add("success");
        message.textContent = `Order #${data.order_id} placed successfully.`;
        event.currentTarget.reset();
        await Promise.all([loadCart(), loadProducts()]);
        setTimeout(() => closeModal(checkoutModal), 700);
        showToast(`Order #${data.order_id} placed · ${money(data.total)}`);
    } catch (error) {
        message.textContent = error.message;
    } finally {
        button.disabled = false;
    }
}

// Page events
searchInput.addEventListener("input", renderProducts);
sortFilter.addEventListener("change", renderProducts);
if (catalogSearch) catalogSearch.addEventListener("input", renderProducts);
if (catalogCategory) catalogCategory.addEventListener("change", renderProducts);
if (catalogSort) catalogSort.addEventListener("change", renderProducts);
$("#shopNowButton").addEventListener("click", () => $("#products").scrollIntoView({ behavior: "smooth" }));
$("#cartButton").addEventListener("click", openCart);
$("#closeCartButton").addEventListener("click", closeCart);
overlay.addEventListener("click", closeCart);
$("#checkoutButton").addEventListener("click", beginCheckout);
$("#loginForm").addEventListener("submit", handleLogin);
$("#registerForm").addEventListener("submit", handleRegister);
$("#checkoutForm").addEventListener("submit", handleCheckout);

authButton.addEventListener("click", () => {
    if (currentUser) logout();
    else openAuth("login");
});

categoryRow.addEventListener("click", (event) => {
    const button = event.target.closest("[data-category]");
    if (!button) return;
    activeCategory = button.dataset.category;
    renderCategories();
    renderProducts();
});

document.addEventListener("click", (event) => {
    const addButton = event.target.closest("[data-add-id]");
    if (addButton) addToCart(addButton.dataset.addId);

    const viewButton = event.target.closest(".view-product");
    if (viewButton) openProduct(viewButton.dataset.id);

    const qtyButton = event.target.closest("[data-qty-id]");
    if (qtyButton) updateCartQuantity(qtyButton.dataset.qtyId, qtyButton.dataset.quantity);

    const removeButton = event.target.closest("[data-remove-id]");
    if (removeButton) removeCartItem(removeButton.dataset.removeId);

    const authTab = event.target.closest("[data-auth-mode]");
    if (authTab) setAuthMode(authTab.dataset.authMode);

    if (event.target.closest("[data-close-modal]")) {
        closeModal(event.target.closest(".modal"));
    }
});

$$('.modal').forEach((modal) => {
    modal.addEventListener("click", (event) => {
        if (event.target === modal) closeModal(modal);
    });
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeCart();
        $$(".modal.active").forEach(closeModal);
    }
});

updateAuthUI();
loadProducts();
loadCart();
