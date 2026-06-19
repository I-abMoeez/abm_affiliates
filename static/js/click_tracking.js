// Click tracking: intercept affiliate link clicks, call backend, then open link.
(function() {
    function handleClick(e) {
        const a = e.target.closest('a[data-affiliate-url][data-product-id]');
        if (!a) return;

        e.preventDefault();

        const productId = a.getAttribute('data-product-id');
        const affiliateUrl = a.getAttribute('data-affiliate-url');

        fetch('/track-click', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    productId: Number(productId),
                    affiliateUrl: affiliateUrl
                })
            })
            .catch(() => {})
            .finally(() => {
                window.open(affiliateUrl, '_blank', 'noopener');
            });
    }

    document.addEventListener('click', handleClick, true);
})();