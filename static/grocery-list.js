var recipeRowIds = new Set();

function populateSelect(selectId, options) {
  const sel = document.getElementById(selectId);

  var opt = document.createElement("option");
  opt.setAttribute("selected", "true");
  opt.setAttribute("value", "");
  opt.setAttribute("disabled", "");
  opt.text = "-- select an option --";
  sel.add(opt);

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


function addTableRow(tableId, options) {
  const tbl = document.getElementById(tableId);
  const idTimePart = (new Date()).getTime();
  const idRandPart = Math.floor(10000000 * Math.random() / 2);

  // add me to the list
  const id = (idTimePart + idRandPart).toString(16).slice(2);
  recipeRowIds.add(id);

  // the new row
  var row = document.createElement("tr");
  row.id = `recipe-row-${id}`;
  tbl.appendChild(row);

  // delete me
  var delCell = document.createElement("td");
  row.appendChild(delCell);

  // the selector cell
  var selCell = document.createElement("td");
  row.appendChild(selCell);

  // the count cell
  var cntCell = document.createElement("td");
  row.appendChild(cntCell);

  // the delete
  var del = document.createElement("button");
  del.setAttribute('class', "btn btn-primary");
  del.innerHTML = "<i class=\"bi bi-dash-square\"></i>";
  del.setAttribute('onclick', `minusRow('${id}')`);
  delCell.appendChild(del);

  // the recipe selection drop down
  var sel = document.createElement("select");
  var selId = `recipe-select-${id}`;
  sel.setAttribute('id', selId);
  selCell.appendChild(sel);
  populateSelect(selId, options);

  // the recipe count drop down
  var cnt = document.createElement("input");
  var cntId = `recipe-count-${id}`;
  cnt.setAttribute('id', cntId);
  cnt.value = 1;
  cnt.type = "number"
  cnt.min = 1;
  cnt.setAttribute('class', "form-control");
  cntCell.appendChild(cnt);
}

function plusRow() {
  addTableRow("recipe-table-body", recipe_list);
}

function minusRow(rowId) {
  if (recipeRowIds.size > 1) {
    var row = document.getElementById(`recipe-row-${rowId}`);
    row.remove();
    recipeRowIds.delete(rowId);
  }
}

function getRecipeIds() {
  var recipeIds = [];
  for (const id in recipeRowIds) {
    var selId = `recipe-select-${id}`;
    var recipe = document.getElementById(selId);
    recipeIds.push(recipe.value);
  }

  return recipeIds;
}

function getRecipeCounts() {
  var recipeCnts = [];
  for (const id in recipeRowIds) {
    var selId = `recipe-count-${id}`;
    var recipe = document.getElementById(selId);
    recipeCnts.push(recipe.value);
  }

  return recipeCnts;
}

function getGroceryListPrint() {
  var recipeIds = getRecipeIds();
  var recipeCnts = getRecipeCounts();

  var newUrl = "/recipe-site/grocery-list-print/";
  newUrl = newUrl + "?recipe_ids=" + recipeIds.join(",");
  newUrl = newUrl + "&recipe_quantities=" + recipeCnts.join(",");
  document.location.href = newUrl;
}

function onLoadPage() {
  addTableRow("recipe-table-body", recipe_list);
}
