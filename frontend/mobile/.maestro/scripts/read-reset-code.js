// Czyta ostatni kod resetu hasła wysłany na EMAIL z API MailHoga.
const response = http.get(
  `${MAILHOG_URL}/api/v2/search?kind=to&limit=1&query=${encodeURIComponent(EMAIL)}`,
);
const body = json(response.body).items[0].Content.Body;
const match = body.match(/^\s*([A-Z0-9]{4}-[A-Z0-9]{4})\s*$/m);
if (!match) throw new Error("Brak kodu resetu w ostatnim mailu");
output.resetCode = match[1];
