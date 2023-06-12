function initContentBlockGrid() {
  function allGrids() {
    return document.querySelectorAll("[data-max-cols]");
  }

  // The minimum width in pixels for our columns
  const defaultColWidth = 320;
  // The maximum number of columns in our grid
  const defaultMaxCols = 4;

  function resizeGrid(grid) {
    // Calculate the number of cols we can have.
    const gridWidth = grid.getBoundingClientRect().width;

    // Get the colWidth from data attribute if possible
    let colWidth = grid.dataset.colWidth || defaultColWidth;
    colWidth = parseInt(colWidth);

    // This is the maximum number of cols we can have if they are all colWidth.
    let cols = Math.floor(gridWidth / colWidth);

    // Get the maxCols from data attribute if possible
    let maxCols = grid.dataset.maxCols || defaultMaxCols;
    maxCols = parseInt(maxCols);

    // Clamp this to our maxCols.
    cols = Math.min(maxCols, cols);

    // Set the number of cols in the grid
    grid.style.gridTemplateColumns = "repeat(" + cols + ", 1fr)";

    // Update grid-column spans limiting them to the number of cols we have.
    for (let j = 1; j < Math.max(defaultMaxCols, maxCols) + 1; j++) {
      for (const gridItem of grid.getElementsByClassName("w" + j)) {
        gridItem.style.gridColumnEnd = "span " + Math.min(j, cols);
      }
    }
  }

  function resizeAllGrids() {
    for (const grid of allGrids()) {
      resizeGrid(grid);
    }
  }

  window.addEventListener("resize", resizeAllGrids);
  resizeAllGrids();
}
