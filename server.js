// server.js
const express = require('express');
const axios   = require('axios');
require('dotenv').config();

const app  = express();
const key  = process.env.GOOGLE_API_KEY;
const PORT = process.env.PORT || 3000;

// Serve all your HTML/CSS/JS from /public
app.use(express.static('public'));

// API endpoint: /api/schedule?place=...&budget=...
app.get('/api/schedule', async (req, res) => {
  const { place, budget } = req.query;
  if (!place || !budget) return res.json({ error: 'Missing place or budget' });

  // Define categories and budget weights
  const categories = [
    { label:'Breakfast', query:'breakfast restaurant', icon:'🍽️', weight:0.15 },
    { label:'Activity',  query:'tourist attraction',     icon:'🥾',   weight:0.25 },
    { label:'Lunch',     query:'lunch restaurant',       icon:'🍛',   weight:0.20 },
    { label:'Movie',     query:'movie theater',          icon:'🎬',   weight:0.20 },
    { label:'Snacks',    query:'cafe',                   icon:'🍦',   weight:0.10 },
    { label:'Transport', query:'taxi service',           icon:'🚕',   weight:0.10 },
  ];

  try {
    const items = [];
    for (let cat of categories) {
      const cost = Math.round(budget * cat.weight);
      const url  = `https://maps.googleapis.com/maps/api/place/textsearch/json`
                 + `?query=${encodeURIComponent(cat.query + ' in ' + place)}`
                 + `&key=${key}`;
      const resp = await axios.get(url);
      const top  = resp.data.results[0];
      if (top) {
        items.push({
          label:    cat.label,
          icon:     cat.icon,
          cost,
          name:     top.name,
          location: {
            lat: top.geometry.location.lat,
            lng: top.geometry.location.lng
          }
        });
      }
    }
    res.json({ place, budget, items });
  } catch (e) {
    console.error(e);
    res.json({ error: 'API fetch error' });
  }
});

app.listen(PORT, () => {
  console.log(`Server listening on http://localhost:${PORT}`);
});
