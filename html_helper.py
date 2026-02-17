"""HTML helpers."""

from typing import Final

page: Final[
    str
] = """<!DOCTYPE html>
<html lang="en">
<head>
<!-- meta -->
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=0.6">
<meta http-equiv="X-UA-Compatible" content="ie=edge">
<!-- title -->
<title>Orcfax OE Data Demo</title>
<!-- Stylesheets -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.css" type="text/css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.blue.min.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/7.0.1/css/all.min.css" integrity="sha512-2SwdPD6INVrV/lHTZbO2nodKhrnDdJK9/kg2XD1r9uGqPo1cUbujc+IYdlYdEErWNu69gVcYgdxlmVmzTWnetw==" crossorigin="anonymous" referrerpolicy="no-referrer" >
<!-- oracle data feed -->
<link rel="meta" type="application/ld+json" title="custom oracle data - value, avg" href="datafeed_one.json" >
<link rel="meta" type="application/ld+json" title="custom oracle data - epoch hourly" href="datafeed_two.json" >
<link rel="meta" type="application/json" title="public key" href="keys.json" >
<!-- style -->
<style>
    header {
    margin-top: 100px;
    }
    div.title {
    width: 850px;
    margin-right: 50px;
    }
    div.other {
    text-align: center;
    width: 100%;
    padding-left: 20%;
    padding-right: 20%;
    }
    h2.other {
    margin-bottom: 20px;
    }
    footer {
    text-align: center;
    margin-bottom: 50px;
    }
</style>
</head>
<body>
<header></header>
<main class='container' style='width: 850px;'>
    <h1>Custom Oracle Feed</h1>
    <div>
    <p>Widget Data Inc..</p>
    <ul>
        <li>keys: <a href="keys.json">keys.json</a></li>
        <li>microdata (value, mean): <a href="datafeed_one.json">datafeed_one.json</a></li>
        <li>microdata (time): <a href="datafeed_two.json">datafeed_two.json</a></li>
        <li>api: <a href="/docs">docs</a></li>
    </ul>
    </div>
    <br>
    <h2>unique endpoints</h2>
    <div>
    <ul>
        <li>endpoint: <a href="/data">data</a></li>
        <li>endpoint: <a href="/data_debug">data (debug)</a></li>
    </ul>
    </div>
    <br>
    <h2>pluralized endpoints</h2>
    <div>
    <ul>
        <li>endpoint: <a href="/data_plural">data pluralized</a></li>
    </ul>
    </div>
</main>
<footer></footer>
</body>
</html>

"""
