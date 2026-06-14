String slugify(String input) {
  const accents = 'áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ';
  const plain   = 'aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC';
  var s = input.toLowerCase();
  for (var i = 0; i < accents.length; i++) {
    s = s.replaceAll(accents[i], plain[i].toLowerCase());
  }
  s = s.replaceAll(RegExp(r'[^a-z0-9]+'), '_');
  s = s.replaceAll(RegExp(r'^_+|_+$'), '');
  return s;
}

String cityTopic(String city) => 'cidade_${slugify(city)}';
