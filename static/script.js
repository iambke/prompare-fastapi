document.getElementById('compareBtn').addEventListener('click', async () => {
  const prompt = document.getElementById('promptInput').value.trim();
  if (!prompt) return;

  document.getElementById('compareBtn').textContent = 'Comparing...';
  document.getElementById('compareBtn').disabled = true;

  try {
    const res = await fetch('/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt })
    });

    const raw = await res.text();
    const data = JSON.parse(raw);

    if (data.error) {
      alert(data.error);
    } else {
      document.getElementById('groqResponse').textContent = data.groq.output;
      document.getElementById('groqTokens').textContent = data.groq.tokens;
      document.getElementById('groqEmissions').textContent = data.groq.emissions + " g";
      document.getElementById('groqLatency').textContent = data.groq.latency + " ms";

      document.getElementById('deepseekResponse').textContent = data.deepseek.output;
      document.getElementById('deepseekTokens').textContent = data.deepseek.tokens;
      document.getElementById('deepseekEmissions').textContent = data.deepseek.emissions + " g";
      document.getElementById('deepseekLatency').textContent = data.deepseek.latency + " ms";
    }
  } catch (err) {
    console.error("Error parsing or fetching:", err);
    alert("Error talking to backend.");
  } finally {
    document.getElementById('compareBtn').textContent = 'Compare';
    document.getElementById('compareBtn').disabled = false;
  }
});
