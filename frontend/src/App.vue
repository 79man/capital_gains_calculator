<template>
    <div id="app">
        <header class="app-header">
            <h1>Capital Gains Calculator</h1>
            <p>Calculate Indian equity capital gains tax with FIFO lot tracking and grandfathering support</p>
        </header>

        <main class="app-main">
            <CapitalGainsCalculator />
        </main>

        <footer class="app-footer">
            <p>&copy; 2025 Capital Gains Calculator</p>
        </footer>
    </div>
</template>

<script>
import CapitalGainsCalculator from '@/views/CapitalGainsCalculator.vue'

export default {
    name: 'App',
    components: {
        CapitalGainsCalculator
    }
}  
</script>

<style>
#app {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: #f9f9f9;
}

.app-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    text-align: center;
}

.app-header h1 {
    margin: 0 0 0.5rem 0;
    font-size: 2.5rem;
}

.app-header p {
    margin: 0;
    opacity: 0.9;
}

.app-main {
    flex: 1;
    padding: 1rem;
    max-width: 1200px;
    margin: 0 auto;
    width: 100%;
}

.app-footer {
    background: #f8f9fa;
    padding: 1rem;
    text-align: center;
    color: #6c757d;
}
</style>