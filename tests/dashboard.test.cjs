const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { createRequire } = require('node:module');
const { chromium } = createRequire(require('node:path').resolve(__dirname, '../dashboard/package.json'))('playwright');
const http = require('node:http');
const fs = require('node:fs/promises');
const path = require('node:path');
let browser, server, base;
const root = path.resolve(__dirname, '..');
before(async () => {
  server = http.createServer(async (req, res) => {
    try {
      const pathname = new URL(req.url, 'http://localhost').pathname;
      const file = path.join(root, pathname.endsWith('/') ? `${pathname}index.html` : pathname);
      if (!file.startsWith(root + path.sep)) throw Error('invalid path');
      const bytes = await fs.readFile(file);
      res.setHeader('Content-Type', ({'.js':'text/javascript','.css':'text/css','.html':'text/html','.json':'application/json'})[path.extname(file)] || 'text/plain');
      res.end(bytes);
    } catch { res.writeHead(404).end('Not found'); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  base = `http://127.0.0.1:${server.address().port}`;
  browser = await chromium.launch({headless:true, ...(process.env.ASTERIA_BROWSER_CHANNEL ? {channel:process.env.ASTERIA_BROWSER_CHANNEL} : {})});
});
after(async () => { await browser?.close(); await new Promise(resolve => server?.close(resolve)); });
async function open(viewport={width:1440,height:1000}) {
  const page = await browser.newPage({viewport});
  await page.goto(`${base}/dashboard/`);
  await page.waitForFunction(() => !document.querySelector('#status').textContent.includes('Loading'));
  return page;
}

test('all objectives and countries render rates, source lineage, and accessible points', async () => {
  const page = await open();
  const errors=[]; page.on('pageerror', e => errors.push(e.message));
  for(const objective of ['NEW_HIRE_6M','SENIOR_HIRE_12M','REGRETTED_TURNOVER_12M']) {
    await page.selectOption('#objective', objective);
    for(const country of ['BG','GR','IE','IT','PL','RO']) {
      await page.selectOption('#country', country);
      assert.match(await page.locator('#latest-value').innerText(), /\d+\.\d%/);
      assert.ok(await page.locator('#chart circle[tabindex="0"]').count());
      assert.ok(await page.locator('#signals a').count());
    }
  }
  assert.equal(await page.locator('#population-label').innerText(),'Average headcount');
  assert.deepEqual(errors,[]);
  await page.close();
});

test('segment, dates, immature counts, empty ranges, and interval suppression', async () => {
  const page = await open();
  await page.selectOption('#segment','Manager');
  assert.match(await page.locator('#latest-value').innerText(), /%/);
  await page.selectOption('#objective','SENIOR_HIRE_12M');
  await page.fill('#date-from','2025-01'); await page.locator('#date-from').dispatchEvent('change');
  assert.match(await page.locator('#status').innerText(), /No mature observations/);
  assert.ok(Number((await page.locator('#censored').innerText()).replaceAll(',',''))>0);
  assert.equal(await page.locator('#latest-value').innerText(),'—');
  await page.fill('#date-from','2021-01'); await page.locator('#date-from').dispatchEvent('change');
  await page.selectOption('#indicator','job_vacancy_rate');
  assert.match(await page.locator('#relationship-note').innerText(),/3 country averages/);
  assert.doesNotMatch(await page.locator('#relationship-stat').innerText(),/95% interval/);
  await page.fill('#date-from','2026-01'); await page.locator('#date-from').dispatchEvent('change');
  assert.match(await page.locator('#status').innerText(), /start date/);
  await page.close();
});

test('keyboard tooltip and responsive layout', async () => {
  const page = await open({width:390,height:844});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true);
  const point=page.locator('#chart circle').first(); await point.focus();
  await page.waitForSelector('.trend-panel .chart-tooltip.is-visible');
  assert.match(await page.locator('.trend-panel .chart-tooltip').innerText(),/hires retained/);
  await point.press('Escape');
  assert.equal(await page.locator('.trend-panel .chart-tooltip').getAttribute('aria-hidden'),'true');
  await page.screenshot({path:path.join(root,'docs/dashboard-mobile.png'),fullPage:true});
  await page.setViewportSize({width:1440,height:1000});
  await page.locator('#country').focus();
  await page.screenshot({path:path.join(root,'docs/dashboard-desktop.png'),fullPage:true});
  await page.close();
});

for (const mode of ['unavailable','malformed']) test(`graceful ${mode} evidence error`, async () => {
  const page = await browser.newPage();
  await page.route('**/retention_metrics.csv', route => route.fulfill({status:mode==='unavailable'?503:200,body:mode==='unavailable'?'Unavailable':'wrong,column\na,b\n'}));
  await page.goto(`${base}/dashboard/`);
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('failed to load'));
  assert.equal(await page.locator('#content').isVisible(),false);
  await page.close();
});

test('target values and direction come from supplied objective definitions', async () => {
  const page = await browser.newPage();
  const original = await fs.readFile(path.join(root,'data/fixtures/retention_objectives.csv'),'utf8');
  await page.route('**/retention_objectives.csv', route => route.fulfill({status:200,body:original.replace('at_most,0.075','at_most,0.001')}));
  await page.goto(`${base}/dashboard/`);
  await page.waitForFunction(()=>!document.querySelector('#content').hidden);
  await page.selectOption('#objective','REGRETTED_TURNOVER_12M');
  assert.equal(await page.locator('#target-copy').innerText(),'at most 0.1%');
  assert.equal(await page.locator('#target-status').innerText(),'Outside target');
  await page.close();
});
