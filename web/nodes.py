from anytree import NodeMixin
from re import findall as re_findall
from os import environ

DOWNLOAD_DIR = environ.get("DOWNLOAD_DIR", "")
if len(DOWNLOAD_DIR) == 0:
    DOWNLOAD_DIR = "/usr/src/app/downloads/"
elif not DOWNLOAD_DIR.endswith("/"):
    DOWNLOAD_DIR += "/"


class TorNode(NodeMixin):
    def __init__(
        self,
        name,
        is_folder=False,
        is_file=False,
        parent=None,
        size=None,
        priority=None,
        file_id=None,
        progress=None,
    ):
        super().__init__()
        self.name = name
        self.is_folder = is_folder
        self.is_file = is_file

        if parent is not None:
            self.parent = parent
        if size is not None:
            self.size = size
        if priority is not None:
            self.priority = priority
        if file_id is not None:
            self.file_id = file_id
        if progress is not None:
            self.progress = progress


def qb_get_folders(path):
    return path.split("/")


def get_folders(path):
    fs = re_findall(f"{DOWNLOAD_DIR}[0-9]+/(.+)", path)[0]
    return fs.split("/")


def make_tree(res, aria2=False):
    parent = TorNode("Torrent")
    if not aria2:
        for i in res:
            folders = qb_get_folders(i.name)
            if len(folders) > 1:
                previous_node = parent
                for j in range(len(folders) - 1):
                    current_node = next(
                        (k for k in previous_node.children if k.name == folders[j]),
                        None,
                    )
                    if current_node is None:
                        previous_node = TorNode(
                            folders[j], parent=previous_node, is_folder=True
                        )
                    else:
                        previous_node = current_node
                TorNode(
                    folders[-1],
                    is_file=True,
                    parent=previous_node,
                    size=i.size,
                    priority=i.priority,
                    file_id=i.id,
                    progress=round(i.progress * 100, 5),
                )
            else:
                TorNode(
                    folders[-1],
                    is_file=True,
                    parent=parent,
                    size=i.size,
                    priority=i.priority,
                    file_id=i.id,
                    progress=round(i.progress * 100, 5),
                )
    else:
        for i in res:
            folders = get_folders(i["path"])
            priority = 1
            if i["selected"] == "false":
                priority = 0
            if len(folders) > 1:
                previous_node = parent
                for j in range(len(folders) - 1):
                    current_node = next(
                        (k for k in previous_node.children if k.name == folders[j]),
                        None,
                    )
                    if current_node is None:
                        previous_node = TorNode(
                            folders[j], parent=previous_node, is_folder=True
                        )
                    else:
                        previous_node = current_node
                TorNode(
                    folders[-1],
                    is_file=True,
                    parent=previous_node,
                    size=i["length"],
                    priority=priority,
                    file_id=i["index"],
                    progress=round(
                        (int(i["completedLength"]) / int(i["length"])) * 100, 5
                    ),
                )
            else:
                TorNode(
                    folders[-1],
                    is_file=True,
                    parent=parent,
                    size=i["length"],
                    priority=priority,
                    file_id=i["index"],
                    progress=round(
                        (int(i["completedLength"]) / int(i["length"])) * 100, 5
                    ),
                )
    return create_list(parent, ["", 0])


"""
def print_tree(parent):
    for pre, _, node in RenderTree(parent):
        treestr = u"%s%s" % (pre, node.name)
        print(treestr.ljust(8), node.is_folder, node.is_file)
"""


def create_list(par, msg, depth=0):
    def get_readable_file_size(size_in_bytes):
        if size_in_bytes is None: return "0B"
        try:
            size_in_bytes = float(size_in_bytes)
        except ValueError:
            return "0B"
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        index = 0
        while size_in_bytes >= 1024 and index < len(units) - 1:
            size_in_bytes /= 1024
            index += 1
        return f"{size_in_bytes:.2f}{units[index]}" if index > 0 else f"{int(size_in_bytes)}B"
    
    if depth > 0:
        msg[0] += '<div class="ml-4 md:ml-12 pl-2 md:pl-4 border-l border-outline-variant/20 flex flex-col gap-1 mt-1">'
    
    for i in par.children:
        if i.is_folder:
            msg[0] += '<div class="flex flex-col mt-3 mb-1">'
            if i.name != ".unwanted":
                msg[0] += f'''<div class="file-row flex items-center justify-between px-4 py-3 rounded-lg cursor-pointer transition-colors group/row">
    <div class="flex items-center gap-4">
        <input class="neon-checkbox folder-checkbox" type="checkbox" name="foldernode_{msg[1]}">
        <span class="material-symbols-outlined text-secondary-dim group-hover/row:text-secondary transition-colors" style="font-variation-settings: 'FILL' 1;">folder_open</span>
        <span class="font-body text-body-md text-on-surface font-medium" style="word-break: break-all;">{i.name}</span>
    </div>
</div>'''
            create_list(i, msg, depth + 1)
            msg[0] += '</div>'
            msg[1] += 1
        else:
            checked = "checked" if i.priority != 0 else ""
            size_str = get_readable_file_size(i.size) if hasattr(i, 'size') else "0B"
            progress_str = f" / {i.progress}%" if hasattr(i, 'progress') and i.progress is not None and i.progress > 0 else ""
            
            msg[0] += f'''<div class="file-row flex items-center justify-between px-4 py-2 rounded-lg cursor-pointer">
    <div class="flex items-center gap-4">
        <input {checked} class="neon-checkbox" type="checkbox" name="filenode_{i.file_id}" data-size="{i.size}">
        <span class="material-symbols-outlined text-on-surface-variant text-sm" style="font-variation-settings: 'FILL' 0;">movie</span>
        <span class="font-body text-body-md text-on-surface/90" data-size="{i.size}" style="word-break: break-all;">{i.name}</span>
    </div>
    <span class="font-body text-label-sm text-on-surface-variant shrink-0">{size_str}{progress_str}</span>
    <input type="hidden" value="off" name="filenode_{i.file_id}">
</div>'''

    if depth > 0:
        msg[0] += '</div>'
    return msg


def make_mega_tree(file_list):
    parent = TorNode("MEGA")
    folder_id = 0
    path_to_node = {"": parent}

    folders = sorted(
        [f for f in file_list if f["is_dir"]],
        key=lambda x: x["path"].count("/"),
    )
    for f in folders:
        full_path = f"{f['path']}{f['name']}".rstrip("/")
        if full_path in path_to_node:
            continue
        parent_path = f["path"].rstrip("/")
        parent_node = path_to_node.get(parent_path, parent)
        path_to_node[full_path] = TorNode(
            f["name"],
            is_folder=True,
            parent=parent_node,
            file_id=folder_id,
        )
        folder_id += 1

    for f in file_list:
        if f["is_dir"]:
            continue
        parent_path = f["path"].rstrip("/")
        parent_node = path_to_node.get(parent_path, parent)
        TorNode(
            f["name"],
            is_file=True,
            parent=parent_node,
            size=f["size"],
            priority=1 if f.get("selected", True) else 0,
            file_id=f["id"],
            progress=0,
        )

    return create_list(parent, ["", 0])
