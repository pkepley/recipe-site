function onLoadPage(){
   $("#recipe_list").selectize({
     create: true,
     sortField: "text"
   });
}

function recipeRedirect(){
  var recipe_id = document.querySelector("#recipe_list").value;
  location.href = "/recipe-site/recipe/" + recipe_id
}
