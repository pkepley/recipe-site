var nRecipeRows = 1;

function populateSelect(selectId, options) {
  const sel = document.getElementById(selectId);

  for (var k of Object.keys(options)) {
    var opt = document.createElement("option");
    opt.value = k;
    opt.text = options[k];
    sel.add(opt);
  }

   $("#" + selectId).selectize({
     create: true,
     sortField: "text"
   });
}

function addTableRow(tableId, maxRow, options) {
  const tbl = document.getElementById(tableId);

  // the new row
  var row = document.createElement("tr");
  row.id = `recipe-row-${maxRow}`;
  tbl.appendChild(row);

  // the selector cell
  var selCell = document.createElement("td");
  row.appendChild(selCell);

  // the count cell
  var cntCell = document.createElement("td");
  row.appendChild(cntCell);

  // the recipe selection drop down
  var sel = document.createElement("select");
  var selId = `recipe-select-${maxRow+1}`;
  sel.setAttribute('id', selId);
  selCell.appendChild(sel);
  populateSelect(selId, options);

  // the recipe count drop down
  var cnt = document.createElement("input");
  var cntId = `recipe-count-${maxRow+1}`;
  cnt.setAttribute('id', cntId);
  cnt.value = 1;
  cnt.type = "number"
  cnt.min = 1;
  cntCell.appendChild(cnt);
}

function plusRow() {
  addTableRow("recipe-table", nRecipeRows, recipe_list);
  nRecipeRows += 1;
}

function minusRow() {
  if (nRecipeRows > 1) {
    var rowId = `recipe-row-${nRecipeRows-1}`;
    var row = document.getElementById(rowId);
    row.remove();
    nRecipeRows -= 1;
    console.log(rowId);
  }
}

function getRecipeIds() {
  var recipeIds = [];
  for (var i = 1; i <= nRecipeRows; i++) {
    var selId = `recipe-select-${i}`;
    console.log(selId);
    var recipe = document.getElementById(selId);
    recipeIds.push(recipe.value);
  }

  return recipeIds;
}

function getGroceryListPrint() {
  var recipeIds = getRecipeIds();

  var newUrl = "/recipe-site/grocery-list-print/?recipe_ids=";
  newUrl = newUrl + recipeIds.join(",")
  document.location.href = newUrl
}

function onLoadPage() {
  for (var i = 0; i < nRecipeRows; i++) {
    addTableRow("recipe-table", i, recipe_list);
  }
}
