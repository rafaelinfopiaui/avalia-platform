const { chromium } = require('/private/tmp/av-s04-playwright/node_modules/playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  });
  const context = await browser.newContext({ locale: 'pt-BR', viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  const failedRequests = [];
  const httpErrors = [];
  page.on('console', msg => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
  page.on('pageerror', error => pageErrors.push(String(error)));
  page.on('requestfailed', request => failedRequests.push(`${request.method()} ${request.url()}: ${request.failure()?.errorText}`));
  page.on('response', response => {
    if (response.status() >= 400) httpErrors.push(`${response.status()} ${response.url()}`);
  });

  const evidenceDir = path.resolve('docs/governance/evidence/AV-S04/pacote-execucao-local');
  await page.goto('http://127.0.0.1:5174/login');
  await page.getByLabel('E-mail').fill('browser.avs04@example.com');
  await page.getByLabel('Senha').fill('BrowserAVS04!');
  await page.getByRole('button', { name: 'Entrar' }).click();
  await page.getByRole('heading', { name: 'Suas avaliações' }).waitFor();
  await page.getByRole('link', { name: 'Nova avaliação' }).click();
  await page.getByRole('heading', { name: 'Configure a avaliação' }).waitFor();

  await page.getByLabel('Título da avaliação').fill('AV-S04 navegador real');
  let questionSections = page.locator('section.panel').filter({ has: page.getByRole('heading', { name: /^Questão \d+$/ }) });
  let q1 = questionSections.nth(0);
  await q1.getByLabel('Enunciado').fill('Primeiro enunciado');
  await q1.getByLabel('Resposta de referência').fill('Primeira referência');
  await q1.getByLabel('Valor máximo da questão').fill('2');
  await q1.locator('fieldset').first().getByLabel('Nome').fill('Critério Q1');
  await q1.locator('fieldset').first().getByLabel('Descrição').fill('Descrição Q1');
  await q1.locator('fieldset').first().getByLabel('Pontos máximos').fill('2');

  await page.getByRole('button', { name: '+ Adicionar questão' }).click();
  questionSections = page.locator('section.panel').filter({ has: page.getByRole('heading', { name: /^Questão \d+$/ }) });
  const q2 = questionSections.nth(1);
  await q2.getByLabel('Enunciado').fill('Segundo enunciado');
  await q2.getByLabel('Resposta de referência').fill('Segunda referência');
  await q2.getByLabel('Valor máximo da questão').fill('3');
  await q2.locator('fieldset').first().getByLabel('Nome').fill('Critério Q2');
  await q2.locator('fieldset').first().getByLabel('Descrição').fill('Descrição Q2');
  await q2.locator('fieldset').first().getByLabel('Pontos máximos').fill('3');
  await page.screenshot({ path: path.join(evidenceDir, 'browser_editor_two_questions.png'), fullPage: true });

  await page.getByRole('button', { name: 'Salvar rascunho' }).click();
  await page.getByText('Rascunho salvo.', { exact: false }).waitFor();
  await page.waitForURL(/\/avaliacoes\/[0-9a-f-]+$/);
  const originalUrl = page.url();
  const originalId = originalUrl.split('/').pop();
  questionSections = page.locator('section.panel').filter({ has: page.getByRole('heading', { name: /^Questão \d+$/ }) });
  const savedCriterionNames = await questionSections.locator('fieldset input:not([type="number"])').evaluateAll(inputs => inputs.map(input => input.value));
  if (savedCriterionNames.join('|') !== 'Critério Q1|Critério Q2') {
    throw new Error(`rubrics were not rehydrated after saving the new draft: ${savedCriterionNames.join('|')}`);
  }

  await questionSections.nth(1).getByRole('button', { name: 'Mover acima' }).click();
  await page.getByRole('button', { name: 'Salvar rascunho' }).click();
  await page.getByText('Rascunho salvo.', { exact: false }).waitFor();
  await page.reload();
  await page.getByRole('heading', { name: 'Configure a avaliação' }).waitFor();
  questionSections = page.locator('section.panel').filter({ has: page.getByRole('heading', { name: /^Questão \d+$/ }) });
  const firstStatement = await questionSections.nth(0).getByLabel('Enunciado').inputValue();
  const secondStatement = await questionSections.nth(1).getByLabel('Enunciado').inputValue();
  if (firstStatement !== 'Segundo enunciado' || secondStatement !== 'Primeiro enunciado') {
    throw new Error(`reorder did not persist: ${firstStatement} / ${secondStatement}`);
  }

  await page.getByRole('button', { name: 'Publicar e inserir resposta' }).click();
  await page.waitForURL(new RegExp(`/avaliacoes/${originalId}/resposta$`));
  const select = page.getByLabel('Selecione a questão a ser respondida');
  if ((await select.inputValue()) !== '') throw new Error('question was selected implicitly');
  const submit = page.getByRole('button', { name: 'Solicitar análise da IA' });
  if (!(await submit.isDisabled())) throw new Error('answer submit enabled before explicit selection');
  await select.selectOption({ index: 1 });
  if (await submit.isDisabled()) throw new Error('answer submit stayed disabled after explicit selection');
  await page.screenshot({ path: path.join(evidenceDir, 'browser_answer_explicit_selection.png'), fullPage: true });

  await page.goto(originalUrl);
  await page.getByRole('button', { name: 'Clonar para editar' }).waitFor();
  await page.getByRole('button', { name: 'Clonar para editar' }).click();
  await page.waitForURL(url => /\/avaliacoes\/[0-9a-f-]+$/.test(url.pathname) && !url.pathname.endsWith(originalId));
  await page.getByText('Editar rascunho', { exact: true }).waitFor();
  const cloneId = page.url().split('/').pop();
  if (cloneId === originalId) throw new Error('clone navigation retained the original id');
  await page.screenshot({ path: path.join(evidenceDir, 'browser_clone_draft.png'), fullPage: true });

  const apiHttpErrors = httpErrors.filter(item => item.includes('/v1/'));
  if (pageErrors.length || failedRequests.length || apiHttpErrors.length) {
    throw new Error(JSON.stringify({ pageErrors, failedRequests, apiHttpErrors, consoleErrors }, null, 2));
  }
  console.log(`ORIGINAL_ASSESSMENT_ID=${originalId}`);
  console.log(`CLONE_ASSESSMENT_ID=${cloneId}`);
  console.log('TWO_QUESTION_CREATE_GREEN');
  console.log('REORDER_PERSISTENCE_GREEN');
  console.log('PUBLISH_AND_EXPLICIT_SELECTION_GREEN');
  console.log('CLONE_NAVIGATION_GREEN');
  console.log(`NON_API_HTTP_ERRORS=${JSON.stringify(httpErrors.filter(item => !item.includes('/v1/')))}`);
  console.log('BROWSER_REAL_CHROME_GREEN');
  await browser.close();
})().catch(async error => {
  console.error(error.stack || error);
  process.exit(1);
});
