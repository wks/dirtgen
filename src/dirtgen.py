#!/usr/bin/python2
# coding: utf8

import codecs
import collections
import os
import os.path
import sys
import shutil

import markdown
import jinja2
import pygments

try:
    progname, src, dst = sys.argv[:3]
except:
    print u"USAGE: python dirtgen.py <source_dir> <destination_dir>"
    sys.exit(1)

resource_dir = os.path.join(os.path.dirname(__file__), u"..", u"data")

print resource_dir

jinja2_env = jinja2.Environment(loader=jinja2.FileSystemLoader(resource_dir))
template_content = jinja2_env.get_template(u"content-page.html")
template_index = jinja2_env.get_template(u"index.html")

source_suffix = u".notes.md"
target_suffix = u".html"

def unsuffix(n):
    return n[:-len(source_suffix)]

def mkdirs_quiet(p):
    if not os.path.isdir(p):
        os.makedirs(p)

def mkparents_quiet(p):
    mkdirs_quiet(os.path.dirname(p))

src = os.path.normpath(src)
dst = os.path.normpath(dst)

index_pathname = os.path.join(dst, u"index.html")

mkdirs_quiet(dst)

def get_rel_path(p):
    return os.path.relpath(p, src)

def get_back_rel_path(p):
    return os.path.relpath(src, p)

FileNode = collections.namedtuple("FileNode", ["relpath", "title", "link", "rootlink"])
DirNode = collections.namedtuple("DirNode", ["relpath", "entries"])
DirEntry = collections.namedtuple("DirEntry", ["name", "child"])

def dir_to_toc(p):
    relpath = get_rel_path(p)
    backrelpath = get_back_rel_path(p)

    children_names = os.listdir(p)

    def mkentry(n):
        """ name -> (None | DirEntry) """
        child_path = os.path.join(p, n)
        if n.startswith("."):
            return None
        elif os.path.isfile(child_path) and n.endswith(source_suffix):
            child_relpath = os.path.relpath(child_path)
            title = unsuffix(n)
            dst_basename = title+target_suffix
            link = os.path.join(relpath, dst_basename)
            
            child_node = FileNode(relpath = child_relpath,
                                  title = title,
                                  link = link,
                                  rootlink = backrelpath)
            return DirEntry(n, child_node)
        elif os.path.isdir(child_path):
            return DirEntry(n, dir_to_toc(child_path))
        else:
            print u"WHAT THE FUCK IS THIS: %s" % p
            return None

    entries = filter(lambda x: x is not None, map(mkentry, children_names))
    
    return DirNode(relpath=relpath, entries=entries)

print src

toc_tree = dir_to_toc(src)

print toc_tree

def generate_files(t):
    if isinstance(t, DirNode):
        dirname = t.relpath
        for (basename, child) in t.entries:
            if isinstance(child, FileNode):
                src_pathname = os.path.join(src, dirname, basename)
                dst_pathname = os.path.join(dst, child.link)
                generate_file(src_pathname, dst_pathname, child.title, child.rootlink)
            else:
                generate_files(child)

def generate_file(src_pathname, dst_pathname, title, rootlink):
    print src_pathname, u"->", dst_pathname
    try:
        with codecs.open(src_pathname, encoding="utf8") as f:
            content_mkdn = f.read()
        
        content_core_html = markdown.markdown(content_mkdn)
        
        content_html = template_content.render(
            rootlink=rootlink,
            title=title,
            content=content_core_html
        )
        
        mkparents_quiet(dst_pathname)
        
        with codecs.open(dst_pathname, "w", encoding="utf8") as f:
            f.write(content_html)
    except Exception, e:
        print u"Error converting file %s:\n%s"%(src_pathname, e)

generate_files(toc_tree)

def generate_index_page():
    content_html = template_index.render(
        rootlink=u".",
        toc=toc_tree
    )
    
    with codecs.open(index_pathname, "w", encoding="utf8") as f:
        f.write(content_html)

generate_index_page()

def copy_data(src_file, dst_path = u""):
    src_pathname = os.path.join(resource_dir, src_file)
    dst_pathname = os.path.join(dst, dst_path, src_file)
    print src_pathname, "->", dst_pathname
    mkparents_quiet(dst_pathname)
    shutil.copyfile(src_pathname, dst_pathname)

copy_data(u"css/main.css")
copy_data(u"css/normalize.css")
