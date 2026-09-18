/* Selecteur d'indicatif telephonique avec drapeau. Senegal en tete + par defaut,
   le reste par ordre alphabetique. Le drapeau (emoji) est deduit du code ISO. */
(function () {
  var PAYS = [
    ['Afghanistan','AF','93'],['Afrique du Sud','ZA','27'],['Albanie','AL','355'],
    ['Algérie','DZ','213'],['Allemagne','DE','49'],['Andorre','AD','376'],['Angola','AO','244'],
    ['Antigua-et-Barbuda','AG','1268'],['Arabie saoudite','SA','966'],['Argentine','AR','54'],
    ['Arménie','AM','374'],['Australie','AU','61'],['Autriche','AT','43'],['Azerbaïdjan','AZ','994'],
    ['Bahamas','BS','1242'],['Bahreïn','BH','973'],['Bangladesh','BD','880'],['Barbade','BB','1246'],
    ['Belgique','BE','32'],['Belize','BZ','501'],['Bénin','BJ','229'],['Bhoutan','BT','975'],
    ['Biélorussie','BY','375'],['Birmanie (Myanmar)','MM','95'],['Bolivie','BO','591'],
    ['Bosnie-Herzégovine','BA','387'],['Botswana','BW','267'],['Brésil','BR','55'],['Brunei','BN','673'],
    ['Bulgarie','BG','359'],['Burkina Faso','BF','226'],['Burundi','BI','257'],['Cambodge','KH','855'],
    ['Cameroun','CM','237'],['Canada','CA','1'],['Cap-Vert','CV','238'],
    ['Centrafrique','CF','236'],['Chili','CL','56'],['Chine','CN','86'],['Chypre','CY','357'],
    ['Colombie','CO','57'],['Comores','KM','269'],['Congo','CG','242'],
    ['Congo (RDC)','CD','243'],['Corée du Nord','KP','850'],['Corée du Sud','KR','82'],
    ['Costa Rica','CR','506'],["Côte d'Ivoire",'CI','225'],['Croatie','HR','385'],['Cuba','CU','53'],
    ['Danemark','DK','45'],['Djibouti','DJ','253'],['Dominique','DM','1767'],['Égypte','EG','20'],
    ['Émirats arabes unis','AE','971'],['Équateur','EC','593'],['Érythrée','ER','291'],
    ['Espagne','ES','34'],['Estonie','EE','372'],['Eswatini','SZ','268'],['États-Unis','US','1'],
    ['Éthiopie','ET','251'],['Fidji','FJ','679'],['Finlande','FI','358'],['France','FR','33'],
    ['Gabon','GA','241'],['Gambie','GM','220'],['Géorgie','GE','995'],['Ghana','GH','233'],
    ['Grèce','GR','30'],['Grenade','GD','1473'],['Guatemala','GT','502'],['Guinée','GN','224'],
    ['Guinée équatoriale','GQ','240'],['Guinée-Bissau','GW','245'],['Guyana','GY','592'],
    ['Haïti','HT','509'],['Honduras','HN','504'],['Hongrie','HU','36'],['Îles Marshall','MH','692'],
    ['Îles Salomon','SB','677'],['Inde','IN','91'],['Indonésie','ID','62'],['Irak','IQ','964'],
    ['Iran','IR','98'],['Irlande','IE','353'],['Islande','IS','354'],['Israël','IL','972'],
    ['Italie','IT','39'],['Jamaïque','JM','1876'],['Japon','JP','81'],['Jordanie','JO','962'],
    ['Kazakhstan','KZ','7'],['Kenya','KE','254'],['Kirghizistan','KG','996'],['Kiribati','KI','686'],
    ['Koweït','KW','965'],['Laos','LA','856'],['Lesotho','LS','266'],['Lettonie','LV','371'],
    ['Liban','LB','961'],['Libéria','LR','231'],['Libye','LY','218'],['Liechtenstein','LI','423'],
    ['Lituanie','LT','370'],['Luxembourg','LU','352'],['Macédoine du Nord','MK','389'],
    ['Madagascar','MG','261'],['Malaisie','MY','60'],['Malawi','MW','265'],['Maldives','MV','960'],
    ['Mali','ML','223'],['Malte','MT','356'],['Maroc','MA','212'],['Maurice','MU','230'],
    ['Mauritanie','MR','222'],['Mexique','MX','52'],['Micronésie','FM','691'],['Moldavie','MD','373'],
    ['Monaco','MC','377'],['Mongolie','MN','976'],['Monténégro','ME','382'],['Mozambique','MZ','258'],
    ['Namibie','NA','264'],['Nauru','NR','674'],['Népal','NP','977'],['Nicaragua','NI','505'],
    ['Niger','NE','227'],['Nigéria','NG','234'],['Norvège','NO','47'],['Nouvelle-Zélande','NZ','64'],
    ['Oman','OM','968'],['Ouganda','UG','256'],['Ouzbékistan','UZ','998'],['Pakistan','PK','92'],
    ['Palaos','PW','680'],['Palestine','PS','970'],['Panama','PA','507'],
    ['Papouasie-Nouvelle-Guinée','PG','675'],['Paraguay','PY','595'],['Pays-Bas','NL','31'],
    ['Pérou','PE','51'],['Philippines','PH','63'],['Pologne','PL','48'],['Portugal','PT','351'],
    ['Qatar','QA','974'],['Roumanie','RO','40'],['Royaume-Uni','GB','44'],['Russie','RU','7'],
    ['Rwanda','RW','250'],['Saint-Marin','SM','378'],['Sainte-Lucie','LC','1758'],
    ['Salvador','SV','503'],['Samoa','WS','685'],['São Tomé-et-Principe','ST','239'],
    ['Sénégal','SN','221'],['Serbie','RS','381'],['Seychelles','SC','248'],['Sierra Leone','SL','232'],
    ['Singapour','SG','65'],['Slovaquie','SK','421'],['Slovénie','SI','386'],['Somalie','SO','252'],
    ['Soudan','SD','249'],['Soudan du Sud','SS','211'],['Sri Lanka','LK','94'],['Suède','SE','46'],
    ['Suisse','CH','41'],['Suriname','SR','597'],['Syrie','SY','963'],['Tadjikistan','TJ','992'],
    ['Tanzanie','TZ','255'],['Tchad','TD','235'],['Tchéquie','CZ','420'],['Thaïlande','TH','66'],
    ['Timor oriental','TL','670'],['Togo','TG','228'],['Tonga','TO','676'],['Trinité-et-Tobago','TT','1868'],
    ['Tunisie','TN','216'],['Turkménistan','TM','993'],['Turquie','TR','90'],['Tuvalu','TV','688'],
    ['Ukraine','UA','380'],['Uruguay','UY','598'],['Vanuatu','VU','678'],['Vatican','VA','379'],
    ['Venezuela','VE','58'],['Viêt Nam','VN','84'],['Yémen','YE','967'],['Zambie','ZM','260'],
    ['Zimbabwe','ZW','263']
  ];

  // Vraie image de drapeau (rendue partout, y compris Windows, contrairement aux
  // emojis drapeaux qui n'y apparaissent pas).
  function flagUrl(iso) { return 'https://flagcdn.com/24x18/' + iso.toLowerCase() + '.png'; }

  var sel = document.getElementById('telPays');   // <select> d'origine (remplace)
  var num = document.getElementById('telNumero');
  var cache = document.getElementById('telephone');
  if (!num || !cache) return;

  // Senegal en tete + par defaut, puis le reste par ordre alphabetique.
  var reste = PAYS.filter(function (p) { return p[1] !== 'SN'; })
                  .sort(function (a, b) { return a[0].localeCompare(b[0], 'fr'); });
  var ordonne = PAYS.filter(function (p) { return p[1] === 'SN'; }).concat(reste);
  var current = ordonne[0];   // Senegal

  var CHEV = '<svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>';

  // --- Construction du selecteur personnalise (drapeau + indicatif) ---
  var wrap = document.createElement('div'); wrap.className = 'cc';
  var btn = document.createElement('button'); btn.type = 'button'; btn.className = 'cc-btn';
  btn.setAttribute('aria-label', 'Indicatif du pays');
  var panel = document.createElement('div'); panel.className = 'cc-panel'; panel.hidden = true;
  var search = document.createElement('input'); search.type = 'text';
  search.className = 'cc-search'; search.placeholder = 'Rechercher un pays...';
  var list = document.createElement('ul'); list.className = 'cc-list';

  function renderBtn() {
    btn.innerHTML = '<img class="cc-flag" src="' + flagUrl(current[1]) + '" alt="" '
      + 'onerror="this.style.display=\'none\'"><span class="cc-code">+' + current[2] + '</span>' + CHEV;
  }

  ordonne.forEach(function (p) {
    var li = document.createElement('li'); li.className = 'cc-item'; li.tabIndex = 0;
    li.innerHTML = '<img src="' + flagUrl(p[1]) + '" alt="" loading="lazy" '
      + 'onerror="this.style.visibility=\'hidden\'"><span class="cc-name">' + p[0]
      + '</span><span class="cc-dial">+' + p[2] + '</span>';
    function choisir() { current = p; renderBtn(); fermer(); maj(); }
    li.addEventListener('click', choisir);
    li.addEventListener('keydown', function (e) { if (e.key === 'Enter') choisir(); });
    list.appendChild(li);
  });

  panel.appendChild(search); panel.appendChild(list);
  wrap.appendChild(btn); wrap.appendChild(panel);
  if (sel) { sel.parentNode.insertBefore(wrap, sel); sel.remove(); }
  else { num.parentNode.insertBefore(wrap, num); }
  renderBtn();

  function ouvrir() { panel.hidden = false; search.value = ''; filtrer(''); search.focus(); }
  function fermer() { panel.hidden = true; }
  btn.addEventListener('click', function (e) { e.stopPropagation(); panel.hidden ? ouvrir() : fermer(); });
  document.addEventListener('click', function (e) { if (!wrap.contains(e.target)) fermer(); });
  function filtrer(q) {
    q = q.toLowerCase().trim();
    [].forEach.call(list.children, function (li) {
      li.style.display = (!q || li.textContent.toLowerCase().indexOf(q) >= 0) ? '' : 'none';
    });
  }
  search.addEventListener('input', function () { filtrer(search.value); });

  function maj() {
    var n = num.value.replace(/\s+/g, ' ').trim();
    cache.value = n ? ('+' + current[2] + ' ' + n) : '';
  }
  num.addEventListener('input', maj);
  var form = num.closest('form');
  if (form) form.addEventListener('submit', maj);
  maj();
})();
