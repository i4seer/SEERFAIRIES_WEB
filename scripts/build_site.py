"""Build the independent Seer Fairies static website. Standard library only.
Run from any directory: python scripts/build_site.py
Optional --source C:/SEERFAIRIES refreshes available print covers and jacket text (Pillow required).
"""
from pathlib import Path
from urllib.parse import quote
import argparse,hashlib,html,json,re,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path)
args=parser.parse_args()
config=json.loads((ROOT/'data/site.json').read_text(encoding='utf-8'))
books=json.loads((ROOT/'data/books.json').read_text(encoding='utf-8'))
e=lambda text:html.escape(str(text),quote=True)
def save(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding='utf-8',newline='\n')
def book_type(b):
    text=re.sub(r'^(?:A|An) ', '',b['copy']['BOOK TYPE'])
    return text[0].upper()+text[1:]
if args.source:
    from PIL import Image
    for b in books:
        directory=args.source/f'book{b["number"]:02}'
        art=directory/'images-print/cover-print-ready-no-barcode.png'
        copy_path=directory/'images-print/background-text.txt'
        if art.exists():
            meta=json.loads((directory/'build-metadata.json').read_text(encoding='utf-8'))['print']
            image=Image.open(art).convert('RGB');dpi=meta['dpi']
            assert image.size==(meta['cover_width_px'],meta['cover_height_px'])
            left=image.width-round((meta['trim_width_in']+meta['bleed_in'])*dpi);top=round(meta['bleed_in']*dpi)
            crop=[left,top,left+round(meta['trim_width_in']*dpi),top+round(meta['trim_height_in']*dpi)]
            front=image.crop(crop);size=[900,round(front.height*900/front.width)]
            b['cover']=f'/assets/covers/{b["slug"]}.webp'
            front.resize(tuple(size),Image.Resampling.LANCZOS).save(ROOT/b['cover'].lstrip('/'),'WEBP',quality=89,method=6)
            front.save(ROOT/f'assets/covers/{b["slug"]}.jpg',quality=92,optimize=True)
            b['size']=size;b['source_art']=art.relative_to(args.source).as_posix();b['source_crop']=crop
        if copy_path.exists():
            raw=copy_path.read_text(encoding='utf-8')
            front=[p.strip() for p in re.split(r'\n\s*\n',raw.split('--- BACK COVER ---')[0].strip())]
            back=[p.strip() for p in re.split(r'\n\s*\n',raw.split('--- BACK COVER ---')[1].split('--- SPINE ---')[0].strip())]
            back=back[:next(i for i,p in enumerate(back) if p.startswith('B. CARTER'))]
            b['copy']={'FRONT TAGLINE':front[2],'BOOK TYPE':front[4],'BACK HOOK':back[0],'BACK KICKER':back[1],'BACK BLURB':'\n\n'.join(back[2:-1]),'BACK CLOSING':back[-1]}
            b['source_copy']=copy_path.relative_to(args.source).as_posix();b['copy_kind']='approved cover text'
    save(ROOT/'data/books.json',json.dumps(books,ensure_ascii=False,indent=2)+'\n')

groups=config['groups']; base=config['base_url'].rstrip('/'); routes=[]
status_labels={'published':'Available now','review':'In review','outlined':'Outlined','planned':'Planned','forthcoming':'Forthcoming'}
for b in books:
    b['available']=b['status']=='published'
    b['status_label']=status_labels[b['status']]
    assert not b['available'] or b['kindle'] or b['paperback'], b['title']
    assert all(b['copy'].get(key) for key in ['FRONT TAGLINE','BOOK TYPE','BACK HOOK','BACK KICKER','BACK BLURB','BACK CLOSING'])
available=[b for b in books if b['available']]
upcoming=[b for b in books if not b['available']]
def version(path):
    return path+'?v='+hashlib.sha256((ROOT/path.lstrip('/')).read_bytes()).hexdigest()[:12]
def paragraphs(text):
    return ''.join('<p>'+e(' '.join(part.splitlines()))+'</p>' for part in re.split(r'\n\s*\n',text.strip()))
def brand():
    return '<a class="brand" href="/" aria-label="Seer Fairies home"><span>SEER</span><strong>FAIRIES</strong></a>'
def header(active):
    links=[('/', 'Home'),('/books/','Books'),('/the-seer/','The Seer'),('/about/','About'),('/news/','News')]
    return '<header class="site-header"><div class="header-inner">'+brand()+'<button class="menu-btn" type="button" aria-expanded="false" aria-controls="main-nav">Menu</button><nav id="main-nav" class="main-nav" aria-label="Main navigation">'+''.join(f'<a href="{url}"'+(' aria-current="page"' if label.lower()==active else '')+'>'+label+'</a>' for url,label in links)+'</nav></div></header>'
def footer():
    return '''<footer class="footer"><div class="shell footer-grid"><div>'''+brand()+'''<p>Dark folklore by B. Carter. Ancient bargains, forgotten rules, and a complete case in every book.</p></div><div><h3>Explore</h3><a href="/books/">All books</a><a href="/books/?status=published">Available now</a><a href="/the-seer/">The Seer</a><a href="/about/">About the author</a><a href="/news/">News</a></div><div><h3>More Seer</h3><a href="https://seerfrights.com/" target="_blank" rel="noopener">Seer Frights ↗</a><a href="https://seerworlds.com/" target="_blank" rel="noopener">Seer Worlds ↗</a><a href="https://seerwarns.com/" target="_blank" rel="noopener">Seer Warns ↗</a><a href="/other-series/">Explore the other series</a></div><div><h3>Seer Press</h3><a href="/contact/">Contact</a><a href="mailto:press@i4seer.com">Press &amp; review copies</a><a href="mailto:authors@i4seer.com">Write to the author</a><a href="https://www.i4seer.com/" target="_blank" rel="noopener">Publisher website ↗</a></div></div><div class="shell footer-meta"><span>© 2026 Institute for Seer LLC · Stories by B. Carter · Published by Seer Press.</span><span>Every fairy is real. The rules were forgotten.</span></div></footer>'''
def page(route,title,description,content,active='',image='/assets/hero-crossroads.webp',schema=None):
    canonical=f'<link rel="canonical" href="{e(base+route)}"><meta property="og:url" content="{e(base+route)}">' if base else ''
    social_image=(base+version(image)) if base else version(image)
    structured='<script type="application/ld+json">'+json.dumps(schema,ensure_ascii=False).replace('</',r'<\/')+'</script>' if schema else ''
    head=f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#0b1714"><title>{e(title)} — Seer Fairies</title><meta name="description" content="{e(description)}"><meta property="og:site_name" content="Seer Fairies"><meta property="og:type" content="website"><meta property="og:title" content="{e(title)} — Seer Fairies"><meta property="og:description" content="{e(description)}"><meta property="og:image" content="{e(social_image)}"><meta name="twitter:card" content="summary_large_image">{canonical}<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="manifest" href="/site.webmanifest"><link rel="stylesheet" href="{version('/assets/site.css')}">{structured}</head>'''
    document=head+'<body><a class="skip" href="#main">Skip to content</a>'+header(active)+'<main id="main">'+content+'</main>'+footer()+f'<script src="{version("/assets/site.js")}" defer></script></body></html>\n'
    target=ROOT/'404.html' if route=='/404.html' else ROOT/route.strip('/')/'index.html'
    save(target,document)
    if route!='/404.html': routes.append(route)
def hero(title,eyebrow,description,crumbs=''):
    return f'<section class="subhero"><div class="shell">'+(f'<p class="crumbs">{crumbs}</p>' if crumbs else '')+f'<p class="eyebrow">{e(eyebrow)}</p><h1>{e(title)}</h1><p class="lede">{e(description)}</p></div></section>'
def cover(b,loading='lazy',class_name=''):
    if not b['cover']:
        return f'<div class="case-dossier {class_name}" role="img" aria-label="{e(b["title"])} case file; cover artwork forthcoming"><span class="dossier-mark">SEER / FAIRIES</span><span class="dossier-number">CASE {b["number"]:02}</span><strong>{e(b["title"])}</strong><span class="dossier-footer">B. CARTER<small>Cover artwork forthcoming</small></span></div>'
    return f'<img class="{class_name}" src="{version(b["cover"])}" width="{b["size"][0]}" height="{b["size"][1]}" loading="{loading}" decoding="async" alt="{e(b["title"])} — Seer Fairies cover">'
def edition_buttons(b,compact=False):
    return ''.join(f'<a class="btn '+('btn-dark' if label=='Kindle' else 'btn-outline')+f'" href="{url}" target="_blank" rel="noopener" aria-label="{e(b["title"])} — {label} on Amazon">{label}'+(' ↗' if compact else ' on Amazon ↗')+'</a>' for label,url in [('Kindle',b['kindle']),('Paperback',b['paperback'])] if url)
def status(b):
    return '<span class="status status-'+e(b['status'])+'">'+e(b['status_label'])+'</span>'
def card(b,catalog=False):
    info=' '.join([b['title'],b['copy']['FRONT TAGLINE'],b['copy']['BACK KICKER'],b['copy']['BACK BLURB'],groups[b['group']]])
    return f'<article class="book-card"'+(f' data-book data-genre="{b["group"]}" data-status="{b["status"]}" data-search="{e(info)}"' if catalog else '')+f'><a class="book-art" href="/books/{b["slug"]}/" aria-label="Explore {e(b["title"])}">{cover(b)}</a>{status(b)}<h{2 if catalog else 3}><a href="/books/{b["slug"]}/">{e(b["title"])}</a></h{2 if catalog else 3}><p class="genre-label">{e(book_type(b))}</p><p class="card-tagline">{e(b["copy"]["FRONT TAGLINE"])}</p><a class="text-link" href="/books/{b["slug"]}/">Open the case →</a></article>'
def available_feature(b):
    return f'<article class="available-book"><a class="available-art" href="/books/{b["slug"]}/" aria-label="Explore {e(b["title"])}">{cover(b)}</a><div><p class="eyebrow">Case {b["number"]:02} · Available now</p><h3><a href="/books/{b["slug"]}/">{e(b["title"])}</a></h3><p class="available-setting">{e(b["copy"]["BACK KICKER"])}</p><p>{e(b["copy"]["FRONT TAGLINE"])}</p><div class="actions">{edition_buttons(b,True)}</div><a class="text-link" href="/books/{b["slug"]}/">Inside the case →</a></div></article>'

home='''<section class="hero" aria-labelledby="hero-title"><picture class="hero-picture"><img src="'''+version('/assets/hero-crossroads.webp')+'''" width="1672" height="941" alt="A lone black horse watches a wet woodland crossroads in the blue-green dusk" fetchpriority="high"></picture><div class="shell hero-content"><div class="hero-copy"><p class="eyebrow light">Dark folklore · B. Carter</p><h1 id="hero-title">Every fairy is real.<br><em>The rules were<br>forgotten.</em></h1><p class="lede">Old-world creatures followed their people across the sea. The bargains survived. The people who remembered them did not.</p><div class="actions"><a class="btn btn-gold" href="/books/">Open the case files →</a><a class="btn btn-light" href="/books/?status=published">Available now</a></div><p class="hero-footnote">A complete mystery in every book. Begin anywhere.</p></div></div></section><section class="reader-strip" aria-label="About the collection"><div class="shell"><p><strong>Old folklore. New ground.</strong><span>Forgotten compacts in familiar places.</span></p><p><strong>Every case stands alone.</strong><span>No required reading order.</span></p><p><strong>Follow the field notes.</strong><span>The signs. The rules. The cost.</span></p></div></section>'''
home+='<section class="section section-white"><div class="shell"><div class="section-top"><div><p class="eyebrow">Available in Kindle &amp; paperback</p><h2>The first signs are here.</h2></div><a class="text-link" href="/books/?status=published">All published books →</a></div><div class="available-grid">'+''.join(available_feature(b) for b in available)+'</div></div></section>'
lanes={'thresholds':'A road, a mine, a boundary someone stopped keeping.','water':'Quiet pools, dangerous shores, and lights beyond the path.','hearth':'An empty bowl. An old barn. A house that remembers.','gifts':'Talent, laughter, beauty—and what they ask in return.'}
home+='<section class="section section-dark"><div class="shell editorial"><div><p class="eyebrow">Where the old world waits</p><h2>At the crossroads.<br>Under the water.<br>Inside the house.</h2><p>The fae came with the families who knew their rules. Generations later, the stories have become superstitions. The agreements are still binding.</p><a class="text-link" href="/the-seer/">Meet the compact-keeper →</a></div><nav class="genre-list" aria-label="Browse the case files">'+''.join(f'<a href="/books/?genre={key}"><div><strong>{e(label)}</strong><small>{e(lanes[key])}</small></div><span aria-hidden="true">↗</span></a>' for key,label in groups.items())+'</nav></div></section>'
home+='<section class="section"><div class="shell"><div class="section-top"><div><p class="eyebrow">Further into the folklore</p><h2>More rules to remember.</h2></div><a class="text-link" href="/books/">Explore every case →</a></div><div class="shelf">'+''.join(card(books[i]) for i in [3,6,7,11])+'</div></div></section>'
home+='''<section class="section section-white"><div class="shell note-layout"><div><p class="eyebrow">A note from the author</p><blockquote>“I write the kind of books I enjoy — full of wonder, big questions, and just enough answers to keep the pages turning.”</blockquote><p class="signature">B. Carter</p></div><div><h2>Leave the<br>hall light on.</h2><p>A little curiosity. A little unease. And always another story waiting beyond the familiar.</p><a class="text-link" href="/about/">About the author →</a></div></div></section>'''
page('/','Dark folklore by B. Carter','Explore Seer Fairies: standalone dark folklore mysteries by B. Carter. Ancient fae, forgotten bargains, and a complete case in every book.',home,'home')

catalog=hero('Choose your way in.','The Seer Fairies case files','Ancient creatures. Familiar places. Each book follows a complete case, with no required reading order. Find published editions or explore the cases still to come.')
catalog+='''<section class="section"><div class="shell"><form id="book-filters" class="catalog-toolbar" role="search" aria-label="Find a case"><div class="field"><label for="book-search">Search the case files</label><input id="book-search" name="q" type="search" placeholder="Creature, title, or place…" autocomplete="off"></div><div class="field"><label for="book-genre">Where will you go?</label><select id="book-genre" name="genre"><option value="">Every kind of place</option>'''+''.join(f'<option value="{key}">{e(label)}</option>' for key,label in groups.items())+'''</select></div><div class="field"><label for="book-status">Publication status</label><select id="book-status" name="status"><option value="">All cases</option><option value="published">Available now</option><option value="forthcoming">Forthcoming</option></select></div></form><div class="filter-summary"><p id="book-count" role="status" aria-live="polite">'''+str(len(books))+''' cases to explore</p><button id="reset-filters" class="reset-filter" type="button">Clear filters</button></div><p id="catalog-empty" class="catalog-empty" hidden>No cases match those filters. Try another word or clear the filters to explore the collection.</p><div class="catalog-grid">'''+''.join(card(b,True) for b in books)+'''</div></div></section>'''
page('/books/','Books','Browse Seer Fairies by creature, setting, or publication status. Find Kindle and paperback editions and explore forthcoming cases.',catalog,'books')

for b in books:
    cp=b['copy'];route=f'/books/{b["slug"]}/';art=b['cover'] or '/assets/hero-crossroads.webp'
    content=hero(b['title'],f'Seer Fairies · Case {b["number"]:02}',book_type(b)+' · By B. Carter',f'<a href="/">Home</a> · <a href="/books/">Books</a> · {e(b["title"])}')
    actions=edition_buttons(b) if b['available'] else '<p class="publication-note">Forthcoming. Publication news and edition links will appear here when this case is available.</p>'
    caption='Current cover artwork · B. Carter' if b['cover'] else 'Case file · Cover artwork forthcoming'
    content+=f'<section class="section"><div class="shell book-layout"><div class="book-media">{cover(b,"eager","book-cover")}<p class="cover-caption">{caption}</p></div><article class="book-content"><p class="eyebrow">{e(b["status_label"])} · Reads standalone</p><h2 class="book-title">{e(b["title"])}</h2><p class="book-tagline">{e(cp["FRONT TAGLINE"])}</p><div class="actions">{actions}<a class="text-link" href="/books/">All case files →</a></div><section class="story-panel" aria-labelledby="story-title"><h3 id="story-title">'+('Inside the case' if b['cover'] else 'Case overview')+f'</h3><p class="eyebrow">{e(cp["BACK KICKER"])}</p><div class="story-hook">'+''.join('<p>'+e(line)+'</p>' for line in cp['BACK HOOK'].splitlines() if line.strip())+'</div><div class="story-copy">'+paragraphs(cp['BACK BLURB'])+'</div><p class="story-closing">'+e(cp['BACK CLOSING'])+'</p></section>'
    content+=f'<dl class="book-facts"><div><dt>Folklore</dt><dd>{e(book_type(b))}</dd></div><div><dt>Reading order</dt><dd>A complete standalone case</dd></div><div><dt>Setting</dt><dd>{e(cp["BACK KICKER"])}</dd></div><div><dt>Availability</dt><dd>'+('Kindle &amp; paperback' if b['available'] else 'Forthcoming')+'</dd></div></dl><nav class="book-navigation" aria-label="More cases">'
    related=[other for other in books if other['group']==b['group'] and other['slug']!=b['slug']][:2]
    content+=''.join(f'<a href="/books/{other["slug"]}/">'+('← ' if i==0 else '')+e(other['title'])+(' →' if i==1 else '')+'</a>' for i,other in enumerate(related))+'</nav></article></div></section>'
    schema={'@context':'https://schema.org','@type':'Book','name':b['title'],'author':{'@type':'Person','name':'B. Carter'},'publisher':{'@type':'Organization','name':'Seer Press'},'inLanguage':'en','description':cp['FRONT TAGLINE'],'genre':'Dark folkloric mystery','url':base+route,'image':base+art,'isPartOf':{'@type':'BookSeries','name':'Seer Fairies'}}
    page(route,b['title'],cp['FRONT TAGLINE']+' A Seer Fairies mystery by B. Carter.',content,'books',art,schema)

seer=hero('Someone still remembers.','The Seer','A black notebook. An old agreement. A stranger who knows which questions to ask.')
seer+='''<section class="section"><div class="shell about-grid"><article class="about-copy"><p class="eyebrow">The compact-keeper</p><h2>The stories crossed<br>the ocean, too.</h2><p>Families carried their trades, their customs, and their stories into new homes. Something older came with them. The creatures of European folklore found new rivers, new mines, new barns, and new doors to stand behind.</p><p>For a while, people remembered. They left the bowl. They respected the boundary. They knew which sound meant it was time to turn back.</p><p>Then the factories closed, the mines were sealed, and the elders died. The knowing faded. The agreements did not.</p><p>The Seer follows the waking: the last compact-keeper moving between places where ordinary explanations have begun to fail. In each case, a young person notices what everyone else has learned to overlook.</p></article><aside class="about-aside"><p class="eyebrow">Before you begin</p><h3>Every case has its rules.</h3><p>Each book tells a complete mystery. Across the collection, another question gathers: what was carried here, and who will remember how to live beside it?</p><p>You can begin with any creature, any place, any case.</p><a class="text-link" href="/books/">Choose a case →</a></aside></div></section><section class="section section-white"><div class="shell"><div class="section-intro"><p class="eyebrow">The field notes</p><h2>Look closer.<br>Remember what matters.</h2><p>Each book closes with field notes on the entity behind the case. Read the story first, then return to the signs.</p></div><div class="seer-ledger"><article><p class="eyebrow">01</p><h3>The entity</h3><p>What the old stories called it, and how it finds a place in the new world.</p></article><article><p class="eyebrow">02</p><h3>The signs</h3><p>The small details that change an ordinary place into something else.</p></article><article><p class="eyebrow">03</p><h3>The rule</h3><p>The agreement people once knew—and what forgetting can set in motion.</p></article><article><p class="eyebrow">04</p><h3>The cost</h3><p>What a bargain asks, and why knowing the rule is only the beginning.</p></article></div></div></section>'''
page('/the-seer/','The Seer','Meet the compact-keeper behind Seer Fairies. Discover the forgotten bargains, folklore, and field notes that connect these standalone mysteries.',seer,'the seer')

about=hero('Wonder has a darker edge.','About Seer Fairies','Dark folklore. Forgotten rules. Stories by B. Carter.')
about+='''<section class="section"><div class="shell about-grid"><article class="about-copy"><p class="eyebrow">The collection</p><h2>Old stories have<br>long memories.</h2><p>Seer Fairies is a collection of dark folkloric mysteries for upper middle-grade and younger teen readers. Each book follows a different creature, a different community, and a young person who begins to notice the signs.</p><p>These are the fae of old bargains and dangerous boundaries: the thing at the river, the noise beneath the mine, the presence inside the house. The fear grows from precise details and rules that people have stopped understanding.</p><p>Every case stands alone. Read for the mystery, the folklore, or the larger thread of the Seer moving through a world that has forgotten its oldest agreements.</p><a class="text-link" href="/the-seer/">Follow the Seer →</a></article><aside class="about-aside"><p class="eyebrow">A reader’s note</p><h3>Begin anywhere.</h3><ul><li>Each book tells a complete case.</li><li>There is no required reading order.</li><li>Expect unease, mystery, and escalating dread.</li><li>Field notes follow each story.</li><li>Available editions link directly to Amazon.</li></ul></aside></div></section><section class="section section-white"><div class="shell about-grid"><article class="author-note"><p class="eyebrow">A note from B. Carter</p><h2>About the author</h2><p>I write the kind of books I enjoy — full of wonder, big questions, and just enough answers to keep the pages turning.</p><p>When I’m not writing, I’m usually reading, walking, or staring at the sky, letting a new idea take shape.</p><p>I live with too many books, not enough shelves, and a strong policy of leaving the hall light on.</p><p>Thanks for joining the journey. There’s always more to see.</p><p class="signature">B. Carter</p></article><div class="about-copy"><p class="eyebrow">Published by Seer Press</p><h2>There’s always<br>more to see.</h2><p>Seer Press is a publishing imprint of Institute for Seer LLC. Its books move between fantasy, folklore, suspense, and adventure.</p><p>For review copies, rights, interviews, or questions about the collection, visit the contact page.</p><div class="actions"><a class="btn btn-dark" href="/contact/">Get in touch</a><a class="text-link" href="/other-series/">Other Seer series →</a></div></div></div></section>'''
page('/about/','About','Meet B. Carter and discover Seer Fairies, standalone dark folklore mysteries published by Seer Press.',about,'about')

news=hero('From the edge of the woods.','Seer Fairies · News','Publication updates, new case files, and more to discover.')
news+='''<section class="section"><div class="shell"><article class="news-entry"><p class="news-date"><time datetime="2026-10-22">October 22, 2026</time> · Publication update</p><h2>The first cases are published.</h2><p class="lede">The Púca, The Sluagh, and The Each-Uisge are available in Kindle and paperback.</p><p>Follow a borrowed face into the Appalachian hills, listen for what moves above the treetops, or approach a quiet pool with care. Each title is a complete mystery, and each edition is linked below.</p><div class="news-books">'''
for b in available:
    news+=f'<article class="news-book"><a href="/books/{b["slug"]}/">{cover(b)}</a><div><p class="eyebrow">Available now</p><h3><a href="/books/{b["slug"]}/">{e(b["title"])}</a></h3><div class="actions">'+''.join(f'<a href="{url}" target="_blank" rel="noopener" aria-label="{e(b["title"])} — {label}">{label} ↗</a>' for label,url in [('Kindle',b['kindle']),('Paperback',b['paperback'])])+'</div></div></article>'
news+='''</div></article><article class="news-entry"><p class="news-date">Collection news · October 2026</p><h2>A home for the case files.</h2><p>Seer Fairies now has a dedicated site. Explore the current covers, read the premise behind each case, and follow publication updates as more books become available.</p><p>The collection continues with further creatures and forgotten agreements. Forthcoming cases are marked throughout the catalog; purchase links will be added when editions are published.</p><a class="text-link" href="/books/?status=forthcoming">Explore forthcoming cases →</a></article></div></section>'''
page('/news/','News','The Púca, The Sluagh, and The Each-Uisge are published in Kindle and paperback. Find edition links and Seer Fairies publication news.',news,'news')

contact=hero('A line to Seer Press.','Contact','Questions about the books, review copies, or the next case? Get in touch.')+'''<section class="section"><div class="shell"><div class="contact-grid"><article class="contact-card"><p class="eyebrow">Press &amp; publishing</p><h2>For the books.</h2><p>Review copies, interviews, rights inquiries, bookseller questions, and other publishing correspondence.</p><a href="mailto:press@i4seer.com">press@i4seer.com</a></article><article class="contact-card"><p class="eyebrow">A note to the author</p><h2>For B. Carter.</h2><p>Reader correspondence and questions about the stories are welcome through the publisher’s author address.</p><a href="mailto:authors@i4seer.com">authors@i4seer.com</a></article></div></div></section>'''
page('/contact/','Contact','Contact Seer Press about Seer Fairies review copies, rights, interviews, or correspondence for B. Carter.',contact)

other=hero('More places to begin.','The wider Seer catalog','Other worlds, other warnings, and other ways to turn the next page.')+'<section class="section"><div class="shell other-series">'
for name,url,label,description in [('Seer Stories','https://www.i4seer.com/standalone/','Standalone fiction','Different lives, different places, and a complete story in every book.'),('Seer Frights','https://seerfrights.com/','Middle-grade horror','Ordinary places, dangerous rules, and the kind of scare that keeps the pages turning.'),('Seer Worlds','https://seerworlds.com/','Middle-grade fantasy','One curious Dot explores impossible worlds, each with a rule of its own.'),('Seer Warns','https://seerwarns.com/','Adult literary suspense','In Harmon, a stranger names what is coming. The warning is believed. The choice is made anyway.'),('Journey','https://seerjourneys.com/','Middle-grade adventure','Sam Calder grows up one year at a time along a road the maps forgot.')]:
    other+=f'<a href="{url}" target="_blank" rel="noopener"><p class="eyebrow">{label}</p><h2>{name} ↗</h2><p>{description}</p></a>'
other+='</div></section>'
page('/other-series/','Other Seer series','Explore more fiction by B. Carter, published by Seer Press.',other)
page('/404.html','Page not found','Find your way back to the Seer Fairies case files.','''<section class="lost"><div class="shell narrow"><p class="eyebrow light">Beyond the path · 404</p><h1>A wrong turn<br>in the woods.</h1><p>This page could not be found. Return to the case files and choose another way in.</p><div class="actions"><a class="btn btn-gold" href="/books/">Open the case files →</a><a class="btn btn-light" href="/">Back home</a></div></div></section>''')
save(ROOT/'routes.json',json.dumps(routes,indent=2)+'\n')
save(ROOT/'robots.txt','User-agent: *\nAllow: /\nSitemap: '+base+'/sitemap.xml\n')
xml=ET.Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
for route in routes:
    node=ET.SubElement(xml,'url');ET.SubElement(node,'loc').text=base+route
save(ROOT/'sitemap.xml','<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(xml,encoding='unicode')+'\n')
save(ROOT/'site.webmanifest',json.dumps({'name':'Seer Fairies','short_name':'Seer Fairies','start_url':'/','display':'standalone','background_color':'#0b1714','theme_color':'#0b1714','icons':[{'src':'/assets/favicon.svg','sizes':'any','type':'image/svg+xml'}]},indent=2)+'\n')
save(ROOT/'assets/favicon.svg','<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#0b1714"/><path d="M20 49V15h25v4H25v11h17v4H25v15" fill="#c3d1b0"/><circle cx="46" cy="47" r="3" fill="#c3b2d1"/></svg>\n')
print(f'Built {len(routes)+1} pages, {len(books)} cases, {len(available)} published titles.')
