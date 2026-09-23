// easier — background worker.
//
// 1. Fetches the current job's answers from the local server apply.py runs while a job is open,
//    for content.js. The extension has host permission for 127.0.0.1, so this request isn't
//    subject to the job site's CORS or local-network rules the way a page request would be.
// 2. The toolbar button: the autofill runs by itself on the job boards listed in manifest.json;
//    on any other page (a company's own careers site, say) clicking the easier icon runs the
//    same autofill there, in every frame, since some forms are embedded.

const SERVER = "http://127.0.0.1:8765/easier.json";

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (!msg || msg.type !== "easier-data") return;
  fetch(SERVER, { cache: "no-store" })
    .then((res) => res.json())
    .then((data) => sendResponse({ ok: true, data }),
          (e) => sendResponse({ ok: false, error: `${e.name}: ${e.message}` }));
  return true; // the reply comes asynchronously
});

chrome.action.onClicked.addListener(async (tab) => {
  const target = { tabId: tab.id, allFrames: true };
  // Tells content.js this run was asked for, so it reports a problem instead of staying quiet.
  await chrome.scripting.executeScript({ target, func: () => { window.__easierManual = true; } });
  await chrome.scripting.executeScript({ target, files: ["content.js"] });
});
