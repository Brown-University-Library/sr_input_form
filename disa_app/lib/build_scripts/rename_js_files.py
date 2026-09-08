"""
Usage:
- $ cd /to/project_root (where manage.py is)
- $ uv run ./disa_app/lib/build_scripts/rename_js_files.py
"""

import os
import logging
import pprint
import re
import subprocess
import hashlib


logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s', 
    datefmt='%d/%b/%Y %H:%M:%S' )
log = logging.getLogger(__name__)


EXCLUDES = [
    'hilitor.js',
    'lunr.min.js',
    'moment.js',
    'tabulator.js',
    'tagify.min.js',
    'tinymce-vue.js',
]


class Renamer():

    def __init__(self) -> None:
        self.tracker_dict = {}
        self.js_dir_path = ''   # set in get_relevant_file_paths()
        self.html_list = []     # set in get_relevant_html_paths()
        self.js_list = []       # set in get_relevant_file_paths()

    def manage_renames( self, project_directory ):
        """ Controller function.
            Called by dunder-main. """
        log.debug( 'starting manage_renames()' )
        ## prep list relevant files ---------------------------------
        self.get_relevant_js_paths( project_directory )     # initializes self.tracker_dict
        self.get_html_paths( project_directory )   # initializes self.html_list
        ## run file-renames -----------------------------------------
        for filename, file_info in self.tracker_dict.items():
            new_filename = self.rename_file( filename, file_info )  # `new_filename` will be '' if no rename needed
            ## rename references ------------------------------------
            self.update_js_list()  # updates self.js_list -- to be used by rename_js_references()
            self.rename_js_references( filename, new_filename )  
            self.rename_html_references( filename, new_filename )
        return

    ## main helper functions ----------------------------------------

    def get_relevant_js_paths( self, project_dir_path: str ) -> None:
        """ Compiles list of relevant file-paths.
            Initializes tracker-dict.
            Called by manage_renames() """
        log.debug( f'project_dir_path, ``{project_dir_path}``' ); assert type(project_dir_path) == str
        ## identify js-directory ------------------------------------
        js_dir_path = os.path.join(project_dir_path, "disa_app/static/js/"); assert type(js_dir_path) == str
        log.debug( f'js_dir_path, ``{js_dir_path}``' )
        if not os.path.exists(js_dir_path):
            raise Exception( f"Directory ``{js_dir_path}`` does not exist." )
        self.js_dir_path = js_dir_path
        ## identify relevant files ----------------------------------
        dir_contents: list = os.listdir(js_dir_path)
        log.debug( f'dir_contents, ``{pprint.pformat(dir_contents)}``' )
        for entry in dir_contents:
            log.debug( f'processing entry, ``{entry}``' )
            if entry.endswith('.js'):
                if entry in EXCLUDES:
                    log.debug( f'skipping excluded file, ``{entry}``' )
                    continue
                ## add to tracker-dict ------------------------------
                self.tracker_dict[entry] = {}
                self.tracker_dict[entry]['file_path'] = os.path.join(js_dir_path, entry)
        log.debug( f'tracker_dict after initialization, ``{pprint.pformat(self.tracker_dict)}``' )
        return
    
    def get_html_paths( self, project_dir_path: str ) -> None:
        """ Gets list of html paths.
            Called by manage_renames() """
        html_dir_path = os.path.join(project_dir_path, "disa_app/disa_app_templates"); assert type(html_dir_path) == str
        log.debug( f'html_dir_path, ``{html_dir_path}``' )
        ## identify relevant files ----------------------------------
        for dirpath, dirnames, filenames in os.walk( project_dir_path ):
            for filename in filenames:
                ## check for .html file -
                if filename.endswith( '.html' ):
                    ## get full path --------------------------------
                    full_path = os.path.join(dirpath, filename)
                    ## add to list ----------------------------------
                    self.html_list.append(full_path)
        log.debug( f'self.html_list after initialization, ``{pprint.pformat(self.html_list)}``' )
        return
    
    def rename_file( self, filename: str, file_info: dict ) -> str:
        """ Coordinates filename rename step.
            Called by manage_renames(). """
        log.debug( 'starting rename_file()' ); assert type(filename) == str; assert type(file_info) == dict
        file_path: str = file_info['file_path']; assert type(file_path) == str
        log.debug( f'processing file_path, ``{file_path}``' )
        ## determine pre-existing hash ------------------------------
        pre_existing_hash: str = self.determine_pre_existing_hash( filename ); assert type(pre_existing_hash) == str
        ## determine actual hash ------------------------------------
        actual_hash: str = self.determine_md5_hash( file_path ); assert type(actual_hash) == str
        ## rename file if needed ------------------------------------
        new_filename: str = self.rename_if_needed( filename, file_path, pre_existing_hash, actual_hash ); assert type(new_filename) == str
        # log.debug( f'tracker_dict after rename, ``{pprint.pformat(self.tracker_dict)}``' )    
        return new_filename

    def update_js_list( self ) -> None:
        """ Compiles simple js-paths for renaming js-references.
            Called by manage_renames() """
        log.debug( 'starting update_js_list()' )
        new_js_list = []
        ## identify relevant files ----------------------------------
        dir_contents: list = os.listdir( self.js_dir_path )
        log.debug( f'dir_contents, ``{pprint.pformat(dir_contents)}``' )
        for entry in dir_contents:
            log.debug( f'processing entry, ``{entry}``' )
            if entry.endswith('.js'):
                if entry in EXCLUDES:
                    log.debug( f'skipping excluded file, ``{entry}``' )
                    continue
                ## add to self.js_list ------------------------------
                new_js_list.append( os.path.join(self.js_dir_path, entry) )
        self.js_list = new_js_list
        log.debug( f'self.js_list, ``{pprint.pformat(self.js_list)}``' )
        return

    def rename_js_references( self, original_filename: str, new_filename: str ) -> None:
        """ Renames references in js files.
            Called by manage_renames() """
        log.debug( f'original_filename, ``{original_filename}``; new_filename, ``{new_filename}``' )
        assert type(original_filename) == str; assert type(new_filename) == str
        if new_filename:
            for js_path in self.js_list:
                assert type(js_path) == str
                log.debug( f'processing js_path, ``{js_path}``' )
                filedata: str = ''
                with open( js_path, 'r', encoding='utf-8', errors='ignore' ) as f:
                    filedata: str = f.read(); assert type(filedata) == str
                if original_filename in filedata:
                    log.debug( f'found original-filename-reference; will update' )
                    new_data: str = filedata.replace( original_filename, new_filename ); assert type(new_data) == str
                    with open( js_path, 'w', encoding='utf-8', errors='ignore' ) as f:
                        f.write( new_data )
                else:
                    log.debug( f'original_filename, ``{original_filename}`` not found in js_path, ``{js_path}``' )
        return

    # def rename_js_references( self, original_filename: str, new_filename: str ) -> None:
    #     """ Renames references in js files.
    #         Called by manage_renames() """
    #     log.debug( f'original_filename, ``{original_filename}``; new_filename, ``{new_filename}``' )
    #     if new_filename:
    #         for filename, file_info in self.tracker_dict.items():
    #             file_path: str = file_info['file_path']; assert type(file_path) == str
    #             log.debug( f'checking for references in file_path, ``{file_path}``' )
    #             try:
    #                 filedata_A: str = ''
    #                 with open( file_path, 'r', encoding='utf-8', errors='ignore' ) as f:
    #                     filedata_A: str = f.read(); assert type(filedata_A) == str
    #                 if original_filename in filedata_A:
    #                     log.debug( f'found original-filename-reference; will update' )
    #                     new_data: str = filedata_A.replace( original_filename, new_filename ); assert type(new_data) == str
    #                     with open( file_path, 'w', encoding='utf-8', errors='ignore' ) as f:
    #                         f.write( new_data )
    #                 else:
    #                     log.debug( f'original_filename, ``{original_filename}`` not found in original-file-path, ``{file_path}``' )
    #             except Exception as e:
    #                 # log.exception( f'problem renaming references in file, ``{file_path}``; traceback follows, then continuing' )
    #                 log.debug( f'file_path, ``{file_path}`` not found; likely has changed.' )
    #                 new_file_path: str = f'{self.js_dir_path}{new_filename}'
    #                 log.debug( f'checking for references in new_file_path, ``{new_file_path}``' )
    #                 filedata_B: str = ''
    #                 with open( new_file_path, 'r', encoding='utf-8', errors='ignore' ) as f:
    #                     filedata_B: str = f.read(); assert type(filedata_B) == str
    #                 if original_filename in filedata_B:
    #                     log.debug( f'found original-filename-reference; will update' )
    #                     new_data: str = filedata_B.replace( original_filename, new_filename ); assert type(new_data) == str
    #                     with open( new_file_path, 'w', encoding='utf-8', errors='ignore' ) as f:
    #                         f.write( new_file_path )
    #                 else:
    #                     log.debug( f'original_filename, ``{original_filename}`` not found in new-file-path, ``{new_file_path}``' )
    #     return

    def rename_html_references( self, original_filename: str, new_filename: str ) -> None:
        """ Renames references in html files.
            Called by manage_renames() """
        log.debug( f'original_filename, ``{original_filename}``; new_filename, ``{new_filename}``' )
        if new_filename:
            for html_path in self.html_list:
                try:
                    filedata: str = ''
                    with open( html_path, 'r', encoding='utf-8', errors='ignore' ) as f:
                        filedata: str = f.read(); assert type(filedata) == str
                    if original_filename in filedata:
                        log.debug( f'original_filename will be updated to new_filename in html_path, ``{html_path}``' )
                        new_data: str = filedata.replace( original_filename, new_filename ); assert type(new_data) == str
                        with open( html_path, 'w', encoding='utf-8', errors='ignore' ) as f:
                            f.write( new_data )
                except Exception as e:
                    log.exception( f'problem renaming references in html-file, ``{html_path}``; traceback follows; processing continues' )
        return
    
    ## sub-helper functions -------------------------------------

    def determine_pre_existing_hash( self, filename: str ) -> str:
        """ Returns pre-existing hash from filename.
            Called by rename_file() """
        assert type(filename) == str
        pre_existing_hash: str = ''
        match_obj = re.search(r'__(\w+)\.js', filename)
        assert ( match_obj is None ) or ( type(match_obj) == re.Match )
        log.debug( f'match_obj, ``{match_obj}``' )
        if match_obj:
            pre_existing_hash = match_obj.group(1); assert type(pre_existing_hash) == str
            log.debug( f'pre_existing_hash, ``{pre_existing_hash}``' )
        else:
            log.debug( f'no pre-existing hash found in filename, ``{filename}``' )
        return pre_existing_hash

    def determine_md5_hash( self, file_path: str ) -> str:
        """ Returns md5 hash of file.
            Called by rename_file() """
        assert type(file_path) == str
        hash_md5 = hashlib.md5()
        with open( file_path, 'rb' ) as f:
            for chunk in iter( lambda: f.read(4096), b'' ):
                hash_md5.update( chunk )
        return_hash: str = hash_md5.hexdigest(); assert type(return_hash) == str
        log.debug( f'return_hash, ``{return_hash}``' )
        return return_hash

    def rename_if_needed( self, filename: str, file_path: str, pre_existing_hash: str, actual_hash: str ) -> str:
        """ Renames file if needed. 
            Called by rename_file() """
        assert type(filename) == str; assert type(file_path) == str; assert type(pre_existing_hash) == str; assert type(actual_hash) == str
        log.debug( f'filename, ``{filename}``; file_path, ``{file_path}``; pre_existing_hash, ``{pre_existing_hash}``; actual_hash, ``{actual_hash}``')
        new_filename = ''
        base_filename, extension = os.path.splitext( filename ); log.debug( f'base_filename, ``{base_filename}``; extension, ``{extension}``' )
        if pre_existing_hash == '':  # eg "foo.js"
            log.debug( 'no pre-existing hash' )
            new_filename = f'{base_filename}__{actual_hash}{extension}'
        else:
            if pre_existing_hash in base_filename:
                if pre_existing_hash != actual_hash:
                    log.debug( 'hashes do not match; renaming' )
                    new_filename = base_filename.replace(pre_existing_hash, actual_hash) + extension
                else:
                    log.debug( 'hashes match; not renaming' )
                    new_filename = ''
        log.debug( f'new_filename, ``{new_filename}``' )
        ## perform rename -------------------------------------------
        if new_filename:
            new_filepath = os.path.join( os.path.dirname(file_path), new_filename )
            os.rename(file_path, new_filepath)
        return new_filename

    ## end class Renamer()


if __name__ == "__main__":
    log.debug( '\n\nstarting dunder-main' )
    renamer = Renamer()
    PROJECT_DIR_PATH = os.curdir; assert type(PROJECT_DIR_PATH) == str  
    project_dir_fullpath = os.path.abspath(PROJECT_DIR_PATH); assert type(project_dir_fullpath) == str
    log.debug( f'project_dir_fullpath, ``{project_dir_fullpath}``' )
    renamer.manage_renames( project_dir_fullpath )
