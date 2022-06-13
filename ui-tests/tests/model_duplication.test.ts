import { test } from '@jupyterlab/galata';

import { expect } from '@playwright/test';

import * as path from 'path';

test.describe('modell_duplication Visual Regression', () => {
  test.beforeEach(async ({ page, tmpPath}) => {
    await page.contents.uploadDirectory(
        path.resolve(__dirname, "./notebooks"), tmpPath
    )
    await page.filebrowser.openDirectory(tmpPath)
  });

  test("Run cytoscape.ipynb", async ({
    page,
    tmpPath,
  }) => {
    const notebook = "cytoscape.ipynb";
    await page.notebook.openByPath(`${tmpPath}/${notebook}`);
    await page.notebook.activate(notebook);

    const capture = [];
    const cellCount = await page.notebook.getCellCount();

    await page.notebook.runCellByCell({
      onAfterCellRun: async (cellIndex: number) => {
        const cell = await page.notebook.getCellOutput(cellIndex);
        if (cell) {
          capture.push( await cell.screenshot());
        }
      }
    });

    await page.notebook.save()

    for (let i = 0; i < cellCount; i++) {
      const img = `widgets-cell-${i}.png`;
      expect(capture[i]).toMatchSnapshot(img);
    }
  });
});

