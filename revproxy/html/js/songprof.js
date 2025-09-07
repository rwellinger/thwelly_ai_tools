document.addEventListener('DOMContentLoaded', function () {
    async function fetchBillingInfo() {
        try {
            const response = await fetch('/api/song/profil');
            const data = await response.json();

            if (data && data.account_info) {
                document.getElementById('balance').innerText = (data.account_info.balance / 100).toFixed(2);
                document.getElementById('totalSpending').innerText = (data.account_info.total_spending / 100).toFixed(2);
                document.getElementById('requestLimit').innerText = data.account_info.concurrent_request_limit;
                document.getElementById('status').innerText = data.status;

                document.getElementById('billingInfo').style.display = 'block';
                document.getElementById('loading').style.display = 'none';
            } else {
                document.getElementById('loading').innerText = 'Error fetching billing information.';
            }
        } catch (error) {
            document.getElementById('loading').innerText = `Error: ${error.message}`;
        }
    }

    // Funktion erst nach DOM-Load aufrufen
    fetchBillingInfo();
});