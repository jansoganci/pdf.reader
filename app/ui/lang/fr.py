"""French sentences (draft: the two accountants correct the terms). Same keys as `en.py`.

Terms follow the French printed on the papers: "pièce" for a paper (one document of the
dossier), "dossier" for the whole uploaded file.
"""

MESSAGES = {
    # -- the app --------------------------------------------------------------------
    "app.title": "Dossier d’import",

    # -- start screen ---------------------------------------------------------------
    "start.heading": "Voulez-vous lire un nouveau dossier d’import ?",
    "start.intro": "Choisissez un PDF, puis cliquez sur Lire. Rien du dossier précédent n’est affiché ici.",
    "start.uploader": "PDF du dossier d’import",
    "start.read": "Lire ce PDF",
    "start.choose_first": "Choisissez d’abord un PDF.",

    # -- reading screen -------------------------------------------------------------
    "reading.heading": "Lecture du PDF",
    "reading.name": "{name} est en cours de lecture.",
    "reading.wait": "Veuillez patienter. Cela prend environ une minute. Ne fermez pas cette page.",
    "reading.sending": "Envoi du PDF pour lecture…",
    "reading.done": "Lecture terminée",
    "reading.back": "Retour",
    "reject.too_big": "Fichier refusé. La limite est de 30 Mo.",
    "reject.not_pdf": "Fichier refusé. Déposez un seul PDF.",
    "reject.unreadable": "Le fichier n’a pas pu être ouvert.",
    "reject.encrypted": "Fichier refusé. Les PDF chiffrés ne sont pas pris en charge.",
    "reject.too_many_pages": "Fichier refusé. La limite est de {limit} pages.",
    "reject.page_too_large": "Le fichier n’a pas pu être ouvert. Une image de page est trop grande.",

    # -- review screen --------------------------------------------------------------
    "review.cannot_open": "Ce dossier n’a pas pu être ouvert.",
    "review.hide_passed": "Masquer les contrôles réussis",
    "review.show_passed": "Afficher les contrôles réussis",
    "review.export": "Export",
    "header.read_another": "Lire un autre dossier",
    "wordmark.name": "Dossier d’import",
    "wordmark.papers.one": "{n} pièce lue",
    "wordmark.papers.other": "{n} pièces lues",
    "export.csv": "Télécharger le CSV",
    "export.json": "Télécharger le JSON",
    "export.override": "Télécharger malgré tout — les erreurs ne sont pas corrigées",
    "strip.note": "Ne figure sur aucune page. Enregistré avec le bouton Enregistrer de la pièce ouverte, ci-dessous.",
    "page.label": "Page {page} · {position} sur {total} de cette pièce",

    # -- statuses -------------------------------------------------------------------
    "tier.good": "Prêt à télécharger",
    "tier.warn": "À vérifier",
    "tier.crit": "Bloque le téléchargement",
    "edited": "Modifié",
    "banner.crit": "{n} point(s) bloquent le téléchargement tant qu’ils ne sont pas vérifiés.",
    "banner.warn_checks": "{n} point(s) méritent un second regard avant le téléchargement.",
    "banner.warn_values": "{n} valeur(s) méritent un second regard avant le téléchargement.",

    # -- the form -------------------------------------------------------------------
    "form.copied": "Recopié de la page",
    "form.field": "Champ",
    "form.value": "Valeur",
    "form.printed": "Texte imprimé",
    "form.not_on_page": "Absent de la page",
    "form.lines": "Lignes recopiées de la page",
    "form.you_type": "À saisir",
    "form.you_type_note": "Ne figure pas sur le PDF. Laissez une case vide si vous n’avez pas encore la valeur.",
    "form.save": "Enregistrer",
    "form.liquidation_note": "Le numéro de paiement ci-dessus est le numéro de liquidation. La référence SAP reste vide tant que vous ne la saisissez pas.",
    "form.line_codes_note": "Chaque ligne de service ci-dessus a son propre code TVA et son propre code motif.",
    "join.above": "Fusionner avec la pièce ci-dessus",
    "split.after": "Scinder après",
    "split.page": "Page {n}",
    "split.button": "Scinder après cette page",

    # -- totals strip ---------------------------------------------------------------
    "totals.customs_source": "Recopié des pièces douanières",
    "totals.issued_by": "Émis par {who}",
    "totals.not_read": "Non lu",

    # -- pages ----------------------------------------------------------------------
    "pages.none": "Aucune page",
    "pages.one": "Page {first}",
    "pages.range": "Pages {first}–{last}",
    "pages.list": "Pages {list}",

    # -- the papers -----------------------------------------------------------------
    "paper.supplier_invoice": "Facture fournisseur",
    "paper.import_licence": "Titre d’importation",
    "paper.customs_declaration": "Déclaration en douane",
    "paper.customs_liquidation": "Liquidation douanière",
    "paper.carrier_invoice": "Facture de transport",
    "paper.logistics_invoice": "Facture logistique",
    "paper.broker_invoice": "Facture du transitaire",
    "paper.unknown": "Autre page",

    "number.supplier_invoice": "N° de facture",
    "number.import_licence": "N° du titre",
    "number.customs_declaration": "N° de déclaration",
    "number.customs_liquidation": "N° de paiement",
    "number.carrier_invoice": "N° de facture",
    "number.logistics_invoice": "N° de facture",
    "number.broker_invoice": "N° de facture",
    "number.unknown": "Numéro",

    "field.supplier_name": "Émis par",
    "field.document_number": "Numéro",
    "field.document_date": "Date",
    "field.currency": "Devise",
    "field.net_amount": "Montant HT",
    "field.tax_amount": "TVA",
    "field.total_amount": "Total",
    "field.fob_amount": "FOB",
    "field.freight_amount": "Fret",
    "field.customs_value": "Valeur en douane",
    "field.exchange_rate": "Taux de change",
    "field.insurance_amount": "Assurance",
    "field.bill_of_lading": "Connaissement",
    "field.containers": "Conteneurs",
    "field.hs_code": "Code SH",
    "field.package_count": "Colis",
    "field.regime": "Régime",

    # -- values a person types (nothing prints them) --------------------------------
    "manual.order_number": "N° de commande",
    "manual.sap_exchange_rate": "Taux de change à saisir",
    "manual.vendor_code": "Code fournisseur",
    "manual.posting_date": "Date de comptabilisation",
    "manual.tax_code": "Code TVA",
    "manual.reason_code": "Code motif",
    "manual.gl_account": "Compte général",
    "manual.sap_reference": "Référence SAP",

    # -- checks (matched by rule id) ------------------------------------------------
    "check.failed.lines_sum_to_total": "Les lignes de la page ne totalisent pas le montant hors taxe.",
    "check.failed.net_plus_tax": "Le montant HT plus la TVA n’est pas égal au total.",
    "check.failed.fob_plus_freight": "FOB plus fret n’est pas égal au total.",
    "check.failed.supplier_equals_licence": "Le total du fournisseur ne correspond pas au titre d’importation.",
    "check.failed.customs_value_matches": "La valeur en douane n’est pas la même sur les deux pièces douanières.",
    "check.failed.bill_of_lading_matches": "Le connaissement n’est pas le même sur toutes les pièces.",
    "check.failed.containers_match": "Les conteneurs ne sont pas les mêmes sur toutes les pièces.",
    "check.failed.duplicate_invoice_number": "Le même numéro apparaît sur deux pièces.",
    "check.failed.supported_currency": "Cette devise est à vérifier.",
    "check.missing_document": "{paper} ne figurait pas dans ce dossier.",
    "check.passed.lines_sum_to_total": "Les lignes de la facture totalisent le montant hors taxe.",
    "check.passed.fob_plus_freight": "FOB plus fret est égal au total imprimé.",
    "check.passed.net_plus_tax": "Le montant HT plus la TVA est égal au total imprimé.",
    "check.passed.supplier_equals_licence": "Le total du fournisseur est égal au total du titre d’importation.",
    "check.passed.customs_value_matches": "Les valeurs en douane imprimées concordent sur les pièces douanières.",
    "check.passed.bill_of_lading_matches": "Les valeurs du connaissement concordent.",
    "check.passed.containers_match": "Les listes de conteneurs concordent.",
    "check.with_paper": "{paper} : {sentence}",
}
