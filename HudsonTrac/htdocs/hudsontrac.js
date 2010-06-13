jQuery(document).ready(function($) {

  // BUILDS must be set in the template, it is a list of build dicts

  var BUILDS_BY_URLS = {};
  for (var i in BUILDS) {
    var build = BUILDS[i];
    BUILDS_BY_URLS[build.url] = build;
  }
  var callout = null;

  $("ul.builds a").bind({
    mouseenter: function(event) {
      if (!callout) {
        callout = $("<div id='hudson-callout'>")
          .css({position: "absolute", background: "#fdfdaa"})
          .appendTo("body");
      }
      var build = BUILDS_BY_URLS[$(this)[0].href];
      callout
        .css({display: "block",
              left: parseInt(event.pageX) + 16 + "px",
              top: parseInt(event.pageY) - 16 + "px"})
        .append($("<p>").text(build.message))
        .append($("<dl>")
          .append($("<dt>").text(_("Name:")))
          .append($("<dd>").text(build.name))
          .append($("<dt>").text(_("Author:")))
          .append($("<dd>").text(build.author))
        );
    },
    mouseleave: function() {
      callout.hide();
      $("p", callout).remove();
      $("dl", callout).remove();
    }
  });
});
