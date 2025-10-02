let used = [];
let lastLetter = null;
let wordlist = [];
let prettyMap = {};

// Load pre-mapped JSON (with {pretty, norm})
fetch("wordlist.json")
  .then(res => res.json())
  .then(data => {
    data.forEach(item => {
      wordlist.push(item.norm);
      prettyMap[item.norm] = item.pretty;
    });
  });

function normalizeInput(word) {
  // Lowercase + remove spaces, hyphens, punctuation
  return word.toLowerCase().replace(/[^a-z]/g, "");
}

function playWord() {
  const input = document.getElementById("userWord").value.trim();
  const normWord = normalizeInput(input);

  if (!normWord) {
    setResult("⚠️ Please enter a country.");
    return;
  }
  if (!wordlist.includes(normWord)) {
    setResult("❌ Invalid country!");
    return;
  }
  if (used.includes(normWord)) {
    setResult("❌ Already used!");
    return;
  }
  if (lastLetter && normWord[0] !== lastLetter) {
    setResult(`❌ Must start with '${lastLetter}'.`);
    return;
  }

  // Accept user word
  used.push(normWord);
  lastLetter = normWord.slice(-1);
  updateUI();
  setResult(`✅ You played: ${prettyMap[normWord]}`);

  // Bot move
  setTimeout(botMove, 800);
}

function botMove() {
  const candidates = wordlist.filter(
    w => w[0] === lastLetter && !used.includes(w)
  );

  if (candidates.length === 0) {
    setResult("🎉 You win! Bot stuck.");
    return;
  }

  // Random bot
  const botWord = candidates[Math.floor(Math.random() * candidates.length)];
  used.push(botWord);
  lastLetter = botWord.slice(-1);
  updateUI();
  setResult(`🤖 Bot played: ${prettyMap[botWord]}`);
}

function updateUI() {
  document.getElementById("lastLetter").textContent = lastLetter || "-";
  document.getElementById("usedWords").textContent =
    used.map(w => prettyMap[w]).join(", ") || "None";
  document.getElementById("userWord").value = "";
}

function setResult(msg) {
  document.getElementById("result").textContent = msg;
}
