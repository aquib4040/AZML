from logging import getLogger, FileHandler, StreamHandler, INFO, basicConfig
from time import sleep
from qbittorrentapi import NotFound404Error, Client as qbClient
from aria2p import API as ariaAPI, Client as ariaClient
from flask import Flask, request

from web.nodes import make_tree

app = Flask(__name__)

aria2 = ariaAPI(ariaClient(host="http://localhost", port=6800, secret=""))

basicConfig(
    format="[%(asctime)s] [%(levelname)s] - %(message)s",
    datefmt="%d-%b-%y %I:%M:%S %p",
    handlers=[FileHandler("log.txt"), StreamHandler()],
    level=INFO,
)

LOGGER = getLogger(__name__)

page = """
<!DOCTYPE html>
<html class="dark" lang="en">
<head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Torrent File Selector</title>
    <link rel="icon" href="https://graph.org/file/1a6ad157f55bc42b548df.png" type="image/jpg">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet"/>
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
    <script>
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    colors: {
                        background: "#000000",
                        surface: "#0a0a0c",
                        primary: "#a855f7",
                        "primary-dim": "#9333ea",
                        outline: "#27272a",
                        "on-surface": "#fafafa",
                        "on-surface-variant": "#a1a1aa",
                        "secondary": "#3b82f6",
                        "secondary-dim": "#2563eb",
                    },
                    fontFamily: {
                        headline: ["Manrope", "sans-serif"],
                        body: ["Inter", "sans-serif"],
                    }
                }
            }
        }
    </script>
    <style>
        body { background-color: #000000; color: #fafafa; }
        .glass-card {
            background: rgba(10, 10, 12, 0.7);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid #27272a;
        }
        .neon-checkbox {
            appearance: none;
            width: 1.2rem;
            height: 1.2rem;
            border: 1px solid #27272a;
            border-radius: 4px;
            background-color: #000000;
            display: inline-grid;
            place-content: center;
            cursor: pointer;
            position: relative;
            transition: all 0.2s ease-in-out;
        }
        .neon-checkbox::before {
            content: "";
            width: 0.6rem;
            height: 0.6rem;
            transform: scale(0);
            transition: 120ms transform ease-in-out;
            box-shadow: inset 1em 1em #a855f7;
            background-color: CanvasText;
            transform-origin: center;
            clip-path: polygon(14% 44%, 0 65%, 50% 100%, 100% 16%, 80% 0%, 43% 62%);
        }
        .neon-checkbox:checked::before {
            transform: scale(1);
        }
        .neon-checkbox:checked {
            border-color: #a855f7;
            box-shadow: 0 0 10px rgba(168, 85, 247, 0.4);
        }
        .neon-checkbox:indeterminate {
            border-color: #a855f7;
        }
        .neon-checkbox:indeterminate::before {
            content: "";
            width: 0.6rem;
            height: 0.15rem;
            transform: scale(1);
            box-shadow: inset 1em 1em #a855f7;
            clip-path: none;
        }
    </style>
</head>
<body class="antialiased min-h-screen p-4 md:p-8 font-body relative">
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/10 rounded-full blur-[120px] pointer-events-none z-[-1]"></div>
    
    <div class="max-w-4xl mx-auto flex flex-col gap-6">
        <!-- Header -->
        <header class="glass-card rounded-2xl p-4 flex items-center justify-between shadow-xl">
            <div class="flex items-center gap-3">
                <img class="w-10 h-10 rounded-full border border-primary/30 shadow-[0_0_15px_rgba(168,85,247,0.2)]" src="https://graph.org/file/1a6ad157f55bc42b548df.png" alt="logo" />
                <h1 class="font-headline font-extrabold text-xl tracking-tight text-on-surface">Bittorrent Selection</h1>
            </div>
            <div class="flex items-center gap-4 text-on-surface-variant">
                <a href="https://github.com/aquib4040/AZML" target="_blank" class="hover:text-primary transition-colors"><span class="material-symbols-outlined">code</span></a>
                <a href="https://t.me/AlphaBotzChat" target="_blank" class="hover:text-primary transition-colors"><span class="material-symbols-outlined">chat</span></a>
            </div>
        </header>

        <!-- Stats Panel -->
        <div id="sticks" class="glass-card rounded-2xl p-5 flex flex-col sm:flex-row justify-around items-center gap-4 text-center shadow-lg transition-all z-50">
            <div>
                <span class="text-xs uppercase tracking-wider text-on-surface-variant">Selected Files</span>
                <h4 class="font-headline text-lg font-bold text-primary mt-1"><span id="checked_files">0</span> <span class="text-on-surface-variant/50">of</span> <span id="total_files">0</span></h4>
            </div>
            <div class="hidden sm:block w-[1px] h-8 bg-outline"></div>
            <div>
                <span class="text-xs uppercase tracking-wider text-on-surface-variant">Selected Size</span>
                <h4 class="font-headline text-lg font-bold text-primary mt-1"><span id="checked_size">0</span> <span class="text-on-surface-variant/50">of</span> <span id="total_size">0</span></h4>
            </div>
        </div>

        <!-- File List / Selector -->
        <section class="glass-card rounded-2xl p-6 shadow-2xl relative">
            <div class="absolute top-0 left-0 h-[2px] w-full bg-gradient-to-r from-primary/50 to-transparent"></div>
            <form action="{form_url}" onsubmit="return s_validate()" method="POST" class="flex flex-col gap-6">
                <div class="flex flex-col gap-2 rounded-xl bg-black/40 border border-outline p-4 max-h-[60vh] overflow-y-auto">
                    {My_content}
                </div>
                <button type="submit" class="self-center w-full sm:w-1/2 bg-primary hover:bg-primary-dim text-white font-headline font-bold py-3.5 rounded-xl transition-all shadow-[0_0_20px_rgba(168,85,247,0.2)] hover:shadow-[0_0_30px_rgba(168,85,247,0.4)]">
                    Confirm Selection
                </button>
            </form>
        </section>
    </div>

    <!-- Scripts -->
    <script>
        function s_validate() {
            if ($("input[name^='filenode_']:checked").length == 0) {
                alert("Select at least one file!");
                return false;
            }
        }

        $(document).ready(function () {
            docready();
            
            // Toggle folder expansion
            $('.file-row').click(function(e) {
                if ($(e.target).is('input[type="checkbox"]')) {
                    return;
                }
                
                var checkbox = $(this).find('input[type="checkbox"]');
                if (checkbox.length && !checkbox.hasClass('folder-checkbox')) {
                    checkbox.prop('checked', !checkbox.prop('checked')).change();
                    return;
                }
                
                var nextContainer = $(this).next('div');
                if (nextContainer.length) {
                    nextContainer.slideToggle('fast');
                    var icon = $(this).find('.material-symbols-outlined');
                    if (icon.text() === 'folder_open') {
                        icon.text('folder');
                    } else if (icon.text() === 'folder') {
                        icon.text('folder_open');
                    }
                }
            });

            // Checkbox change cascade
            $('input[type="checkbox"]').change(function(e) {
                var isChecked = $(this).prop('checked');
                
                if ($(this).hasClass('folder-checkbox')) {
                    var folderContainer = $(this).closest('.flex-col');
                    folderContainer.find('input[type="checkbox"]').not(this).prop({
                        checked: isChecked,
                        indeterminate: false
                    });
                }
                
                checkingfiles();
                checked_size();
                updateParentCheckboxes();
            });

            function updateParentCheckboxes() {
                $('.flex-col').each(function() {
                    var folderCheckbox = $(this).find('> .file-row input.folder-checkbox');
                    if (folderCheckbox.length === 0) return;
                    
                    var childContainer = $(this).find('> div');
                    if (childContainer.length === 0) return;
                    
                    var childCheckboxes = childContainer.find('input[type="checkbox"]');
                    var total = childCheckboxes.length;
                    var checked = childCheckboxes.filter(':checked').length;
                    var indeterminate = childCheckboxes.filter(function() {
                        return this.indeterminate;
                    }).length;
                    
                    if (checked === total && total > 0) {
                        folderCheckbox.prop({
                            checked: true,
                            indeterminate: false
                        });
                    } else if (checked > 0 || indeterminate > 0) {
                        folderCheckbox.prop({
                            checked: false,
                            indeterminate: true
                        });
                    } else {
                        folderCheckbox.prop({
                            checked: false,
                            indeterminate: false
                        });
                    }
                });
            }

            // Set initial state of parent checkboxes
            updateParentCheckboxes();
        });

        function docready() {
            checked_size();
            checkingfiles();
            
            var fileInputs = $("input[name^='filenode_']");
            $("#total_files").text(fileInputs.length);
            
            var total_size = 0;
            fileInputs.each(function () {
                var size = parseFloat($(this).data("size"));
                if (!isNaN(size)) {
                    total_size += size;
                }
            });
            $("#total_size").text(humanFileSize(total_size));
        }

        function checked_size() {
            var checked_size = 0;
            var checkedboxes = $("input[name^='filenode_']:checked");
            checkedboxes.each(function () {
                var size = parseFloat($(this).data("size"));
                if (!isNaN(size)) {
                    checked_size += size;
                }
            });
            $("#checked_size").text(humanFileSize(checked_size));
        }

        function checkingfiles() {
            var checked_files = $("input[name^='filenode_']:checked").length;
            $("#checked_files").text(checked_files);
        }

        function humanFileSize(size) {
            var i = -1;
            var byteUnits = [' KB', ' MB', ' GB', ' TB', ' PB'];
            do {
                size = size / 1024;
                i++;
            } while (size > 1024);
            return Math.max(size, 0).toFixed(1) + byteUnits[i];
        }

        function sticking() {
            var window_top = $(window).scrollTop();
            var div_top = $('header').offset().top;
            if (window_top > div_top) {
                $('#sticks').addClass('fixed top-4 left-4 right-4 max-w-4xl mx-auto shadow-2xl').removeClass('relative');
            } else {
                $('#sticks').removeClass('fixed top-4 left-4 right-4 max-w-4xl mx-auto shadow-2xl').addClass('relative');
            }
        }

        $(function () {
            $(window).scroll(sticking);
            sticking();
        });
    </script>
</body>
</html>
"""

code_page = """
<!DOCTYPE html>
<html class="dark" lang="en">
<head>
    <meta charset="utf-8"/>
    <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
    <title>Secure Access - KINETIC CORE</title>
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet"/>
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
    <script>
        tailwind.config = {
            darkMode: "class",
            theme: {
                extend: {
                    colors: {
                        background: "#000000",
                        surface: "#0a0a0c",
                        primary: "#a855f7",
                        "primary-dim": "#9333ea",
                        outline: "#27272a",
                        "on-surface": "#fafafa",
                        "on-surface-variant": "#a1a1aa",
                    },
                    fontFamily: {
                        headline: ["Manrope", "sans-serif"],
                        body: ["Inter", "sans-serif"],
                    }
                }
            }
        }
    </script>
    <style>
        body { background-color: #000000; color: #fafafa; }
        .glass-card {
            background: rgba(10, 10, 12, 0.7);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
        }
        .animate-float { animation: float 6s ease-in-out infinite; }
        @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
            100% { transform: translateY(0px); }
        }
        .pin-input:focus {
            box-shadow: 0 0 0 2px rgba(168, 85, 247, 0.2);
        }
    </style>
</head>
<body class="antialiased min-h-screen flex items-center justify-center p-6 relative">
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary/10 rounded-full blur-[120px] pointer-events-none z-[-1]"></div>
    
    <div class="w-full max-w-lg glass-card rounded-2xl border border-outline shadow-2xl overflow-hidden text-center p-10 relative">
        <div class="absolute top-0 left-0 h-[2px] w-full bg-gradient-to-r from-primary-dim via-primary to-transparent"></div>
        
        <div class="w-16 h-16 mx-auto rounded-full bg-surface border border-outline flex items-center justify-center mb-6 animate-float">
            <span class="material-symbols-outlined text-primary text-3xl">lock</span>
        </div>
        
        <h1 class="font-headline text-2xl font-extrabold text-on-surface mb-2">Authorization Required</h1>
        <p class="font-body text-on-surface-variant mb-8">Enter the 4-digit security pin provided in Telegram to access your files.</p>
        
        <form action="{form_url}">
            <div class="mb-8">
                <input 
                    type="text" 
                    name="pin_code"
                    placeholder="Enter 4-digit PIN"
                    class="pin-input w-full bg-black border border-outline rounded-xl px-6 py-4 text-center text-xl font-headline tracking-[0.5em] text-on-surface placeholder:tracking-normal placeholder:text-on-surface-variant/50 focus:border-primary focus:outline-none transition-all"
                    autocomplete="off"
                    maxlength="4"
                    required
                />
            </div>
            
            <button type="submit" class="w-full bg-primary hover:bg-primary-dim text-white font-headline font-bold py-4 rounded-xl transition-all flex items-center justify-center gap-2 group shadow-[0_0_20px_rgba(168,85,247,0.3)] hover:shadow-[0_0_30px_rgba(168,85,247,0.5)]">
                Authenticate
                <span class="material-symbols-outlined group-hover:translate-x-1 transition-transform">arrow_forward</span>
            </button>
        </form>
    </div>
</body>
</html>
"""


def re_verfiy(paused, resumed, client, hash_id):

    paused = paused.strip()
    resumed = resumed.strip()
    if paused:
        paused = paused.split("|")
    if resumed:
        resumed = resumed.split("|")

    k = 0
    while True:
        res = client.torrents_files(torrent_hash=hash_id)
        verify = True
        for i in res:
            if str(i.id) in paused and i.priority != 0:
                verify = False
                break
            if str(i.id) in resumed and i.priority == 0:
                verify = False
                break
        if verify:
            break
        LOGGER.info("Reverification Failed! Correcting stuff...")
        client.auth_log_out()
        sleep(1)
        client = qbClient(host="localhost", port="8090")
        try:
            client.torrents_file_priority(
                torrent_hash=hash_id, file_ids=paused, priority=0
            )
        except NotFound404Error as e:
            raise NotFound404Error from e
        except Exception as e:
            LOGGER.error(f"{e} Errored in reverification paused!")
        try:
            client.torrents_file_priority(
                torrent_hash=hash_id, file_ids=resumed, priority=1
            )
        except NotFound404Error as e:
            raise NotFound404Error from e
        except Exception as e:
            LOGGER.error(f"{e} Errored in reverification resumed!")
        k += 1
        if k > 5:
            return False
    LOGGER.info(f"Verified! Hash: {hash_id}")
    return True


@app.route("/app/files/<string:id_>", methods=["GET"])
def list_torrent_contents(id_):

    if "pin_code" not in request.args.keys():
        return code_page.replace("{form_url}", f"/app/files/{id_}")

    pincode = ""
    for nbr in id_:
        if nbr.isdigit():
            pincode += str(nbr)
        if len(pincode) == 4:
            break
    if request.args["pin_code"] != pincode:
        return "<h1>Incorrect pin code</h1>"

    if len(id_) > 20:
        client = qbClient(host="localhost", port="8090")
        res = client.torrents_files(torrent_hash=id_)
        cont = make_tree(res)
        client.auth_log_out()
    else:
        res = aria2.client.get_files(id_)
        cont = make_tree(res, True)
    return page.replace("{My_content}", cont[0]).replace(
        "{form_url}", f"/app/files/{id_}?pin_code={pincode}"
    )


@app.route("/app/files/<string:id_>", methods=["POST"])
def set_priority(id_):

    data = dict(request.form)
    resume = ""
    if len(id_) > 20:
        pause = ""

        for i, value in data.items():
            if "filenode" in i:
                node_no = i.split("_")[-1]

                if value == "on":
                    resume += f"{node_no}|"
                else:
                    pause += f"{node_no}|"

        pause = pause.strip("|")
        resume = resume.strip("|")

        client = qbClient(host="localhost", port="8090")

        try:
            client.torrents_file_priority(torrent_hash=id_, file_ids=pause, priority=0)
        except NotFound404Error as e:
            raise NotFound404Error from e
        except Exception as e:
            LOGGER.error(f"{e} Errored in paused")
        try:
            client.torrents_file_priority(torrent_hash=id_, file_ids=resume, priority=1)
        except NotFound404Error as e:
            raise NotFound404Error from e
        except Exception as e:
            LOGGER.error(f"{e} Errored in resumed")
        sleep(1)
        if not re_verfiy(pause, resume, client, id_):
            LOGGER.error(f"Verification Failed! Hash: {id_}")
        client.auth_log_out()
    else:
        for i, value in data.items():
            if "filenode" in i and value == "on":
                node_no = i.split("_")[-1]
                resume += f"{node_no},"

        resume = resume.strip(",")

        res = aria2.client.change_option(id_, {"select-file": resume})
        if res == "OK":
            LOGGER.info(f"Verified! GID: {id_}")
        else:
            LOGGER.info(f"Verification Failed! Report! GID: {id_}")
    return list_torrent_contents(id_)


@app.route("/")
def homepage():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AZML</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Exo:wght@300;400;600;700&display=swap');

        body {
            font-family: 'Exo', sans-serif !important;
        }
        
        :root {
            --bg-color: #0a0f1c;
            --primary-blue: #00b7ff;
            --primary-yellow: #ffd700;
            --primary-orange: #ff4500;
            --text-color: #ffffff;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background-color: #000000;
            color: var(--text-color);
            line-height: 1.6;
            min-height: 100vh;
        }

        .container {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 2rem;
            position: relative;
            overflow: hidden;
        }

        .background-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 20%, var(--primary-blue) 0%, transparent 40%),
                radial-gradient(circle at 80% 20%, var(--primary-yellow) 0%, transparent 40%),
                radial-gradient(circle at 50% 80%, var(--primary-orange) 0%, transparent 40%);
            opacity: 0.15;
            filter: blur(70px);
            z-index: 0;
        }

        .content {
            position: relative;
            z-index: 1;
            text-align: center;
            background: rgba(10, 15, 28, 0.7);
            padding: 3rem;
            border-radius: 15px;
            backdrop-filter: blur(20px);
            box-shadow: 
                0 0 30px rgba(0, 183, 255, 0.2),
                inset 0 0 30px rgba(0, 183, 255, 0.1);
            border: 1px solid rgba(0, 183, 255, 0.1);
            animation: contentAppear 1s ease-out;
            max-width: 600px;
            width: 100%;
        }

        @keyframes contentAppear {
            from { 
                opacity: 0; 
                transform: translateY(20px);
                backdrop-filter: blur(0px);
            }
            to { 
                opacity: 1; 
                transform: translateY(0);
                backdrop-filter: blur(20px);
            }
        }

        .logo {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            object-fit: cover;
            margin-bottom: 1.5rem;
            border: 2px solid var(--primary-blue);
            box-shadow: 0 0 20px rgba(0, 183, 255, 0.3);
            animation: logoSpin 15s linear infinite;
        }

        @keyframes logoSpin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        h1 {
            font-size: 3rem;
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 5px;
            background: linear-gradient(45deg, var(--primary-blue), var(--primary-yellow), var(--primary-orange));
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            text-shadow: 0 0 20px rgba(0, 183, 255, 0.3);
        }

        .subtitle {
            font-size: 1.1rem;
            margin-bottom: 2rem;
            color: var(--text-color);
            opacity: 0.9;
        }

        .version {
            font-size: 0.9rem;
            color: var(--primary-blue);
            margin-bottom: 1rem;
            font-weight: 600;
        }

        .links {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .button {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 0.8rem 1.5rem;
            background: linear-gradient(45deg, rgba(0, 183, 255, 0.2), rgba(255, 215, 0, 0.2));
            color: var(--text-color);
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .button:hover {
            transform: translateY(-3px);
            background: linear-gradient(45deg, var(--primary-blue), var(--primary-yellow));
            color: #000000;
            box-shadow: 0 5px 15px rgba(0, 183, 255, 0.4);
            border-color: transparent;
        }

        .copyright {
            margin-top: 2rem;
            font-size: 0.85rem;
            opacity: 0.7;
            color: var(--text-color);
        }

        .tagline {
            font-size: 0.95rem;
            color: var(--primary-yellow);
            margin-top: 1.5rem;
            font-weight: 500;
            letter-spacing: 1px;
        }

        @media (max-width: 480px) {
            .content {
                padding: 2rem 1.5rem;
            }

            h1 {
                font-size: 2.2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="background-animation"></div>
        <div class="content">
            <img class="logo" src="https://graph.org/file/1a6ad157f55bc42b548df.png" alt="AZML Logo">
            <div class="version">V3.0.0</div>
            <h1><b>AZML</b></h1>
            <p class="subtitle">Experience the next generation of workflow automation</p>

            <div class="links">
              <a href="https://t.me/Thealphabotz" target="_blank" class="button">
                <i class="fab fa-telegram-plane"></i> Telegram Channel
              </a>
              <a href="https://t.me/AlphaBotzChat" target="_blank" class="button">
                <i class="fas fa-comments"></i> Support Group
              </a>
              <a href="https://github.com/aquib4040/AZML" target="_blank" class="button">
                <i class="fab fa-github"></i> GitHub Repository
              </a>
            </div>

            <div class="tagline">SIMPLIFY YOUR WORKFLOW, MAXIMIZE YOUR IMPACT!</div>
            <p class="copyright">&copy; 2026 AZML. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""


@app.errorhandler(Exception)
def page_not_found(e):
    return (
        f"<h1>404: Torrent not found! Mostly wrong input. <br><br>Error: {e}</h2>",
        404,
    )


if __name__ == "__main__":
    app.run()
