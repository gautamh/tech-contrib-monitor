<script>
    import { onMount } from 'svelte';
    import { base } from '$app/paths';
    import { slide } from 'svelte/transition';

    // Reactive variables to hold the data for the page
    let clusterEvents = [];
    $: filteredClusterEvents = clusterEvents.filter(item => item.donorCount >= 3);
    let pacContributions = [];
    let lastUpdated = "";
    let expandedItems = {}; // Tracks expanded state for all collapsible sections

     // Request a weekday along with a long date
    const dateOptions = {
        year: "numeric",
        month: "long",
        day: "numeric",
    };

    // Function to calculate the latest contribution date
    function calculateLastUpdated(clusters, pacs) {
        let maxDate = null;

        const allContributions = [];
        clusters.forEach(c => allContributions.push(...c.contributions));
        pacs.forEach(p => allContributions.push(p));

        allContributions.forEach(c => {
            const date = new Date(c.date.replace(/-/g, '/'));
            if (!maxDate || date > maxDate) {
                maxDate = date;
            }
        });

        if (maxDate) {
            lastUpdated = maxDate.toLocaleString('en-US', dateOptions);
        }
    }

    // Function to get the latest contribution date from a cluster
    function getLatestContributionDate(cluster) {
        let maxDate = null;
        cluster.contributions.forEach(c => {
            const date = new Date(c.date.replace(/-/g, '/'));
            if (!maxDate || date > maxDate) {
                maxDate = date;
            }
        });
        return maxDate;
    }

    // Fetch the processed data once the component is mounted in the browser
    onMount(async () => {
        try {
            const response = await fetch(`${base}/data/formatted_contributions.json`);
            if (response.ok) {
                const data = await response.json();
                clusterEvents = data.clusterEvents || [];
                pacContributions = data.pacContributions || [];
                calculateLastUpdated(clusterEvents, pacContributions);

                // Sort clusters by the latest contribution date
                clusterEvents.sort((a, b) => {
                    const dateA = getLatestContributionDate(a);
                    const dateB = getLatestContributionDate(b);
                    return dateB - dateA;
                });
            } else {
                console.error("Failed to load formatted contribution data");
            }
        } catch (e) {
            console.error("Error fetching formatted contribution data:", e);
        }
    });

    // --- Formatting and Helper Functions ---

    const formatCurrency = (amount) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(amount);
    
    // Returns a URL for a company's logo
    const getLogoUrl = (employer) => {
        const name = employer.toLowerCase();
        if (name.includes('google')) return `${base}/logos/google.svg`;
        if (name.includes('meta')) return `${base}/logos/meta.svg`;
        if (name.includes('microsoft')) return `${base}/logos/microsoft.svg`;
        return ''
    };

    // Returns a color hex code based on party name for inline styling
    const getPartyColor = (party) => {
        if (!party) return '#4b5563'; // gray-600
        const lowerParty = party.toLowerCase();
        if (lowerParty === 'democratic party') return '#2563eb'; // blue-600
        if (lowerParty === 'republican party') return '#dc2626'; // red-600
        return '#4b5563'; // gray-600
    };

    // Toggles the visibility of a details section
    function toggleExpanded(key) {
        expandedItems[key] = !expandedItems[key];
    }

    // Groups a list of contributions by month string (e.g., "August 2025")
    function groupByMonth(contributions) {
        if (!contributions || contributions.length === 0) return [];
        const grouped = new Map();
        for (const c of contributions) {
            if (!c.date || typeof c.date !== 'string') continue; // Guard against invalid data
            const date = new Date(c.date.replace(/-/g, '/'));
            const monthYear = date.toLocaleString('en-US', { month: 'long', year: 'numeric' });
            if (!grouped.has(monthYear)) {
                grouped.set(monthYear, []);
            }
            grouped.get(monthYear).push(c);
        }
        return Array.from(grouped.entries());
    }

    // Takes a list of contributions (for a single month) and summarizes them by donor/recipient pair.
    function summarizeContributionsInMonth(contributions) {
        const summary = new Map();
        for (const c of contributions) {
            const key = `${c.donorName}-${c.recipientName}`;
            if (!summary.has(key)) {
                summary.set(key, {
                    donorName: c.donorName,
                    recipientName: c.recipientName,
                    recipientParty: c.recipientParty,
                    positiveAmount: 0,
                    negativeAmount: 0,
                    contributions: []
                });
            }
            const entry = summary.get(key);
            const amount = parseFloat(c.amount);
            if (!isNaN(amount)) {
                if (amount > 0) entry.positiveAmount += amount;
                if (amount < 0) entry.negativeAmount += Math.abs(amount);
            }
            entry.contributions.push(c);
        }

        // Calculate date ranges and counts for each summary group
        return Array.from(summary.values()).map(s => {
            const dates = s.contributions.map(c => new Date(c.date.replace(/-/g, '/')));
            const minDate = new Date(Math.min(...dates));
            const maxDate = new Date(Math.max(...dates));
            let dateRange = minDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            if (minDate.toDateString() !== maxDate.toDateString()) {
                dateRange += ` - ${maxDate.toLocaleDateString('en-US', { day: 'numeric' })}`;
            }
            return { ...s, dateRange, contributionCount: s.contributions.length };
        });
    }

    // --- Tab Switching Logic ---

    function showClusters(e) {
        e.target.classList.add('tab-active');
        document.getElementById('tab-pacs').classList.remove('tab-active');
        document.getElementById('feed-container-clusters').classList.remove('hidden');
        document.getElementById('feed-container-pacs').classList.add('hidden');
    }

    function showPacs(e) {
        e.target.classList.add('tab-active');
        document.getElementById('tab-clusters').classList.remove('tab-active');
        document.getElementById('feed-container-pacs').classList.remove('hidden');
        document.getElementById('feed-container-clusters').classList.add('hidden');
    }
</script>

<svelte:head>
    <title>Campaign Finance Activity Feed</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
</svelte:head>

<body class="bg-gray-100 text-gray-800" style="font-family: 'Inter', sans-serif;">

    <div class="container mx-auto max-w-3xl p-4 sm:p-6 md:p-8">
        
        <header class="mb-6">
            <h1 class="text-3xl font-bold text-gray-900">Tech Contributions Monitor</h1>
            <p class="text-sm text-gray-500 mt-1">Last Recorded Contribution Date: {lastUpdated}</p>
            <p class="text-sm text-gray-500 mt-1">created by <a class="underline" href="https://gautamhathi.com">Gautam Hathi</a></p>
        </header>

        <div class="border-b border-gray-200">
            <nav class="-mb-px flex space-x-6" aria-label="Tabs">
                <button id="tab-pacs" on:click={showPacs} class="tab-active whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm">
                    🏢 Corporate PACs
                </button>
                <button id="tab-clusters" on:click={showClusters} class="text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm">
                    👥 Executive Clusters
                </button>
            </nav>
        </div>

        <!-- Executive Clusters (Individual Contributions) -->
        <div id="feed-container-clusters" class="mt-6 space-y-6 hidden">
            {#if filteredClusterEvents.length > 0}
                {#each filteredClusterEvents as item, i}
                    {@const key = `cluster-${i}`}
                    <div class="bg-orange-50 p-4 sm:p-5 rounded-xl shadow-lg border-2 border-orange-200">
                        <div class="flex items-start space-x-4">
                            <div class="text-2xl pt-2">
                                <img src={getLogoUrl(item.employer)} alt={`${item.employer} logo`} class="h-8 w-8 rounded-full" />
                            </div>
                            <div class="flex-1">
                                <p class="text-sm font-semibold uppercase text-orange-600">Executive Cluster</p>
                                <h3 class="text-lg font-bold mt-1">
                                    <span class="text-gray-900">{formatCurrency(item.totalAmount)}</span> from {item.donorCount} {item.employer} execs
                                </h3>
                                <p class="text-gray-600 mt-1">
                                    to <span class="font-semibold" style="color: {getPartyColor(item.recipientParty)} !important;">{item.recipientName}</span>
                                </p>
                                <div class="mt-3">
                                    <button on:click={() => toggleExpanded(key)} class="text-xs font-semibold text-indigo-600 hover:text-indigo-800">
                                        {expandedItems[key] ? 'Hide' : 'Show'} Details
                                    </button>
                                </div>
                                {#if expandedItems[key]}
                                    <div class="mt-4 bg-white rounded-lg border border-gray-200 p-3" transition:slide>
                                        <ul role="list">
                                            {#each item.contributions as c}
                                                <a href={c.fecUrl} target="_blank" rel="noopener noreferrer" class="block hover:bg-gray-50 rounded-md">
                                                    <li class="flex justify-between items-center py-2 px-2 border-b border-gray-100 last:border-b-0">
                                                        <div>
                                                            <p class="font-medium text-gray-700">{c.donorName}</p>
                                                            <p class="text-xs text-gray-500">{c.donorInfo}</p>
                                                        </div>
                                                        <div class="text-right">
                                                            <p class="font-semibold text-gray-800">{formatCurrency(c.amount)}</p>
                                                            <p class="text-xs text-gray-400">{new Date(c.date.replace(/-/g, '/')).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</p>
                                                        </div>
                                                    </li>
                                                </a>
                                            {/each}
                                        </ul>
                                    </div>
                                {/if}
                            </div>
                        </div>
                    </div>
                {/each}
            {:else}
                <p class="text-center text-gray-500 pt-8">No executive clusters with 3 or more donors found in the current data.</p>
            {/if}
        </div>

        <!-- Corporate PACs (Summarized) -->
        <div id="feed-container-pacs" class="mt-6 space-y-6">
             {#if pacContributions.length > 0}
                {#each groupByMonth(pacContributions) as [month, contributionsInMonth]}
                    <div class="relative py-2">
                        <div class="absolute inset-0 flex items-center" aria-hidden="true">
                            <div class="w-full border-t border-gray-300"></div>
                        </div>
                        <div class="relative flex justify-center">
                            <span class="bg-gray-100 px-3 text-sm font-medium text-gray-600">{month}</span>
                        </div>
                    </div>
                    {#each summarizeContributionsInMonth(contributionsInMonth) as item, i}
                        {@const key = `${month}-${i}`}
                        <div class="bg-white p-4 sm:p-5 rounded-xl shadow-md border-2 border-purple-200">
                            <div class="flex items-start space-x-4">
                                <div class="text-xl pt-1">
                                    <img src={getLogoUrl(item.donorName)} alt={`${item.donorName} logo`} class="h-8 w-8 rounded-full" />
                                </div>
                                <div class="flex-1">
                                    <div class="flex justify-between items-start">
                                        <div>
                                            <p class="text-xs font-semibold uppercase text-purple-600">Corporate PAC Donation</p>
                                            <p class="text-gray-800 mt-1">
                                                <span class="font-semibold">{item.donorName}</span>
                                                {#if item.negativeAmount > 0}
                                                    donated <span class="font-bold text-gray-900">{formatCurrency(item.positiveAmount)}</span> and took back <span class="font-bold text-red-600">{formatCurrency(item.negativeAmount)}</span>
                                                {:else}
                                                    donated <span class="font-bold text-gray-900">{formatCurrency(item.positiveAmount)}</span>
                                                {/if}
                                                <span class="text-sm text-gray-500"> (in {item.contributionCount} contributions)</span>
                                            </p>
                                            <p class="text-gray-600 mt-1">
                                                to <span class="font-semibold" style="color: {getPartyColor(item.recipientParty)} !important;">{item.recipientName}</span>
                                            </p>
                                        </div>
                                        <div class="text-right text-xs text-gray-400 whitespace-nowrap pt-1">{item.dateRange}</div>
                                    </div>
                                    <div class="mt-3">
                                        <button on:click={() => toggleExpanded(key)} class="text-xs font-semibold text-indigo-600 hover:text-indigo-800">
                                            {expandedItems[key] ? 'Hide' : 'Show'} Details
                                        </button>
                                    </div>
                                    {#if expandedItems[key]}
                                        <div data-testid="details-list" class="mt-4 bg-gray-50 rounded-lg border border-gray-200 p-3" transition:slide>
                                            <ul role="list">
                                                {#each item.contributions as c}
                                                    <a href={c.fecUrl} target="_blank" rel="noopener noreferrer" class="block hover:bg-gray-200 rounded-md">
                                                        <li class="flex justify-between items-center py-2 px-2 border-b border-gray-100 last:border-b-0">
                                                            <p class="font-medium text-sm" class:text-red-600={c.amount < 0}>{formatCurrency(c.amount)}</p>
                                                            <p class="text-xs text-gray-500">{new Date(c.date.replace(/-/g, '/')).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</p>
                                                        </li>
                                                    </a>
                                                {/each}
                                            </ul>
                                        </div>
                                    {/if}
                                </div>
                            </div>
                        </div>
                    {/each}
                {/each}
            {:else}
                <p class="text-center text-gray-500 pt-8">No PAC contributions found in the current data.</p>
            {/if}
        </div>
    </div>

</body>

<style>
    .tab-active {
        border-bottom-width: 2px;
        border-color: rgb(79 70 229);
        color: rgb(79 70 229);
    }
</style>