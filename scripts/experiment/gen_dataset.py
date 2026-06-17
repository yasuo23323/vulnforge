import json

DATASET = []

def add(scanner, vuln_type, severity, url, desc, evidence, gt):
    DATASET.append({
        "scanner": scanner, "vuln_type": vuln_type, "severity": severity,
        "url": url, "desc": desc, "evidence": evidence, "gt": gt
    })

# SQL Injection - True Positives
add("sqlmap", "sql_injection", "critical",
    "http://testphp.vulnweb.com/products.php?cat=1",
    "Error-based SQL injection in cat parameter",
    "GET /products.php?cat=1' 200 OK...MySQL Error: You have an error in your SQL syntax",
    "true_positive")

add("sqlmap", "sql_injection", "high",
    "http://testphp.vulnweb.com/login.php",
    "Time-based blind SQL injection in username",
    "POST /login.php...username=admin'+AND+SLEEP(5)--&password=test...Response time: 5.2s",
    "true_positive")

add("nuclei", "sql_injection", "high",
    "http://testphp.vulnweb.com/artists.php?id=1",
    "Union-based SQL injection in id parameter",
    "GET /artists.php?id=1+UNION+SELECT+1,2,3,4,5...200 OK...Numbers 1,2,3,4,5 in output",
    "true_positive")

# SQL Injection - False Positives
add("nuclei", "sql_injection", "high",
    "http://testsite.com/search.php?q=hello",
    "Possible SQLi - generic error page detected",
    "GET /search.php?q=hello'...500 Error...App Error page, no SQL error messages in response",
    "false_positive")

add("sqlmap", "sql_injection", "high",
    "http://ecommerce.site/products?id=456",
    "Possible SQLi - parameter dynamic behavior",
    "GET /products?id=456+AND+1=2...different content but no DB errors, template-based rendering",
    "false_positive")

add("dalfox", "sql_injection", "medium",
    "http://blog.example.com/posts?page=2",
    "SQL warning pattern in user comment",
    "GET /posts?page=2'...'SQL command not properly ended' found in user comment text, not system error",
    "false_positive")

# XSS - True Positives
add("dalfox", "xss", "medium",
    "http://testphp.vulnweb.com/search.php?test=query",
    "Reflected XSS - unescaped script tag",
    "GET /search.php?test=[XSS_PAYLOAD]... 200 OK...Response reflects unencoded [XSS_TAG] in HTML context",
    "true_positive")

add("dalfox", "xss", "high",
    "http://testphp.vulnweb.com/guestbook.php",
    "Stored XSS via comment submission",
    "POST /guestbook.php...name=[XSS_EVIL]...Next page load shows unescaped [XSS_TAG] in comments",
    "true_positive")

# XSS - False Positives
add("nuclei", "xss", "medium",
    "http://testphp.vulnweb.com/search.php?q=hello",
    "Input value reflected in response",
    "GET /search.php?q=[XSS_PAYLOAD]...200 OK...Response contains [XSS_ENCODED] - HTML entities encoded",
    "false_positive")

add("nuclei", "xss", "medium",
    "http://forum.site.com/viewtopic?pid=123",
    "Reflected parameter in JSON API response",
    "GET /viewtopic?pid=[XSS_PAYLOAD]...200 OK...Content-Type: application/json, input in JSON value not HTML",
    "false_positive")

add("dalfox", "xss", "low",
    "http://wiki.site.com/wiki/Page_Name",
    "Parameter in URL path partially encoded",
    "GET /wiki/[XSS_PAYLOAD]...404...partial encoding, Content-Type not text/html",
    "false_positive")

add("nuclei", "xss", "medium",
    "http://cms.site.com/search?q=hello",
    "CSP headers with reflected parameter",
    "GET /search?q=[XSS_PAYLOAD]...200 OK...CSP: default-src 'self' blocks inline script execution",
    "false_positive")

# Path Traversal / LFI - True Positives
add("nuclei", "path_traversal", "high",
    "http://testsite.com/download.php?file=.../.../etc/passwd",
    "LFI via path traversal in file parameter",
    "GET /download.php?file=../../etc/passwd...200 OK...root:x:0:0:root:/root:/bin/bash...",
    "true_positive")

add("ffuf", "path_traversal", "medium",
    "http://ecommerce.site/admin/backup.sql",
    "Exposed backup SQL file via directory brute-force",
    "GET /admin/backup.sql...200 OK...DROP TABLE IF EXISTS users;...SQL backup with user credentials",
    "true_positive")

add("nuclei", "path_traversal", "high",
    "http://testsite.com/includes/page.php?template=about",
    "Local file read via template parameter",
    "GET /page.php?template=../../../etc/passwd...200 OK...root:x:0:0:root:...File read successful",
    "true_positive")

# Path Traversal / LFI - False Positives
add("nuclei", "path_traversal", "high",
    "http://cms.site.com/template.php?file=index",
    "Path traversal attempt - file not found",
    "GET /template.php?file=../../../../etc/passwd...404...App prepends dir and appends .php extension",
    "false_positive")

add("ffuf", "path_traversal", "medium",
    "http://ecommerce.site/images/product.jpg",
    "Directory enumeration via ../ patterns",
    "GET /images/../admin/...302 Found...Path normalization occurs before access check",
    "false_positive")

add("ffuf", "path_traversal", "low",
    "http://cms.site.com/js/jquery.js",
    "Discovered JavaScript file via brute-force",
    "GET /js/jquery.js...200 OK.../*! jQuery v3.6.0 */...Standard library, not sensitive",
    "false_positive")

# SSRF - True Positives
add("nuclei", "ssrf", "critical",
    "http://cloud.site.com/fetch?url=http://169.254.169.254/latest/meta-data/",
    "SSRF to cloud metadata service",
    "GET /fetch?url=http://169.254.169.254/latest/...200 OK...ami-id, instance-id returned",
    "true_positive")

add("nuclei", "ssrf", "high",
    "http://internal.site.com/proxy?url=http://localhost:8080/health",
    "SSRF to internal service",
    "GET /proxy?url=http://localhost:8080/health...200 OK...{'status':'UP'} - internal health check",
    "true_positive")

add("nuclei", "ssrf", "high",
    "http://shop.site.com/load?path=http://evil.com/test",
    "External URL fetch capability detected",
    "GET /load?path=http://evil.com/test...200 OK...External DNS lookup performed, outbound connection made",
    "true_positive")

# SSRF - False Positives
add("nuclei", "ssrf", "medium",
    "http://cms.site.com/import?feed=http://rss.example.com/news.xml",
    "External RSS feed import",
    "GET /import?feed=http://rss.example.com/news.xml...200 OK...RSS feed fetched as designed function",
    "false_positive")

add("nuclei", "ssrf", "medium",
    "http://blog.site.com/avatar?url=http://gravatar.com/avatar.jpg",
    "Avatar URL fetch with domain whitelist",
    "GET /avatar?url=http://gravatar.com/avatar.jpg...200 OK...Only whitelisted domains allowed",
    "false_positive")

add("nuclei", "ssrf", "high",
    "http://api.site.com/webhook?callback=http://requestbin.net/r/test",
    "SSRF via callback parameter (external only)",
    "GET /webhook?callback=http://requestbin.net/r/test...200 OK...External webhook service, no internal access",
    "false_positive")

# Write dataset
with open("scripts/experiment/dataset.py", "w", encoding="utf-8") as f:
    f.write("# VulnForge Experiment Dataset\n")
    f.write("# Ground truth for vulnerability verification experiments\n\n")
    f.write("DATASET = \\\n")
    json.dump(DATASET, f, indent=2, ensure_ascii=False)
    f.write("\n")

print(f"Dataset generated: {len(DATASET)} findings")
for gt_type in ["true_positive", "false_positive"]:
    count = sum(1 for f in DATASET if f["gt"] == gt_type)
    print(f"  {gt_type}: {count}")