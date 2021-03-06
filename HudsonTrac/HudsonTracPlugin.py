# -*- coding: utf-8 -*-
"""
A Trac plugin which interfaces with the Hudson Continuous integration server

You can configure this component via the
[wiki:TracIni#hudson-section "[hudson]"]
section in the trac.ini file.

See also:
 - http://hudson-ci.org/
 - http://wiki.hudson-ci.org/display/HUDSON/Trac+Plugin
"""

import time
import urllib2
from xml.dom import minidom
from datetime import datetime, timedelta

from pkg_resources import resource_filename

from genshi.builder import tag

from trac.core import *
from trac.config import Option, BoolOption
from trac.perm import IPermissionRequestor
from trac.util.datefmt import format_datetime, pretty_timedelta, to_timestamp
from trac.util.text import unicode_quote
from trac.util.translation import domain_functions
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
                            IRequestHandler, add_script, add_stylesheet
from trac.timeline.api import ITimelineEventProvider

add_domain, _, tag_ = domain_functions('hudsontrac',
                                       ('add_domain', '_', 'tag_'))

class Build(dict):
    def __getattr__(self, name):
        return self[name]

class HudsonTracPlugin(Component):
    """Display Hudson results in the timeline and an entry in the main
    navigation bar.
    """
    
    implements(INavigationContributor, ITimelineEventProvider,
               ITemplateProvider, IPermissionRequestor, IRequestHandler)

    disp_mod = BoolOption('hudson', 'display_modules', False, """
 	Display status of modules in the timeline too.

        Note: enabling this may slow down the timeline retrieval significantly
	""")
    job_url  = Option('hudson', 'job_url', 'http://localhost/hudson/', """
        The url of the top-level hudson page if you want to display
        all jobs, or a job or module url (such as
        http://localhost/hudson/job/build_foo/) if you want only
        display builds from a single job or module.  This must be an
        absolute url.""")
    username = Option('hudson', 'username', '',
        'The username to use to access hudson')
    password = Option('hudson', 'password', '',
        'The password to use to access hudson')
    nav_url  = Option('hudson', 'main_page', '/hudson/', """
        The url of the hudson main page to which the trac nav entry
        should link; if empty, this will lead to our own summary page.
        This may be a relative url.""")
    disp_tab = BoolOption('hudson', 'display_in_new_tab', False,
        'Open hudson page in new tab/window')
    alt_succ = BoolOption('hudson', 'alternate_success_icon', False,
        'Use an alternate success icon (green ball instead of blue)')
    use_desc = BoolOption('hudson', 'display_build_descriptions', True, """
        Whether to display the build descriptions for each build
        instead of the canned "Build finished successfully etc."
        messages.""")
    display_building = BoolOption('hudson', 'display_building', False,
        'Also show in-progress builds (pulsating green ball)')

    def __init__(self):
        # i18n
        add_domain(self.env.path, resource_filename(__name__, 'locale'))
        self.log.info("Added domain 'hudsontrac' -> %s",
                      resource_filename(__name__, 'locale'))

        # prepare self.info_url
        api_url = unicode_quote(self.job_url, '/%:@')
        if api_url and api_url[-1] != '/':
            api_url += '/'
        api_url += 'api/xml'

        pwd_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        pwd_mgr.add_password(None, api_url, self.username, self.password)

        b_auth = urllib2.HTTPBasicAuthHandler(pwd_mgr)
        d_auth = urllib2.HTTPDigestAuthHandler(pwd_mgr)

        self.url_opener = urllib2.build_opener(b_auth, d_auth)

        self.env.log.debug("registered auth-handler for '%s', username='%s'",
                           api_url, self.username)

        if '/job/' in api_url:
            path = '/*/build[timestamp>=%(start)s][timestamp<=%(stop)s]'
            depth = 1
            if self.disp_mod:
                path += ('|/*/module/build'
                         '[timestamp>=%(start)s][timestamp<=%(stop)s]')
                depth += 1
        else:
            path = '/*/job/build[timestamp>=%(start)s][timestamp<=%(stop)s]'
            depth = 2
            if self.disp_mod:
                path += ('|/*/job/module/build'
                         '[timestamp>=%(start)s][timestamp<=%(stop)s]')
                depth += 1

        self.info_url = ('%s?xpath=%s&depth=%s'
                         '&exclude=//action|//artifact|//changeSet'
                         '&wrapper=builds' %
                         (api_url.replace('%', '%%'), path, depth))

        self.env.log.debug("Build-info url: '%s'", self.info_url)

    def _get_info(self, start, stop):
        """Retrieve build information from Hudson, in the given period."""
        start = to_timestamp(start)
        stop = to_timestamp(stop)
        url = self.info_url % {'start': start*1000, 'stop': stop*1000}
        try:
            try:
                return minidom.parse(self.url_opener.open(url))
            except Exception:
                import sys
                self.env.log.exception("Error getting build info from '%s'",
                                       url)
                raise IOError(
                    "Error getting build info from '%s': %s: %s. This most " \
                    "likely means you configured a wrong job_url." % \
                    (url, sys.exc_info()[0].__name__, str(sys.exc_info()[1])))
        finally:
            self.url_opener.close()

    def _extract_builds(self, info):
        """Extract build information from XML retrieved from Hudson.

        Returns a list of build dicts.
        """
        if info.documentElement.nodeName != 'builds':
            raise IOError(
                "Error getting build info from '%s': returned document has "
                "unexpected node '%s'. This most likely means you configured "
                "a wrong job_url" % (info_url, info.documentElement.nodeName))

        # xml parsing helpers
        def get_text(node):
            rc = ""
            for node in node.childNodes:
                if node.nodeType == node.TEXT_NODE:
                    rc += node.data
            return rc

        def get_string(parent, child):
            nodes = parent.getElementsByTagName(child)
            return nodes and get_text(nodes[0]).strip() or ''

        def get_number(parent, child):
            num = get_string(parent, child)
            return num and int(num) or 0

        # extract all build entries
        for entry in info.documentElement.getElementsByTagName("build"):
            # ignore builds that are still running
            if get_string(entry, 'building') == 'true':
                if self.display_building:
                    result = 'INPROGRESS'
                else:
                    continue
            else:
                result = get_string(entry, 'result')

            # create timeline entry
            started = get_number(entry, 'timestamp')
            if result == 'INPROGRESS':
                # we hope the clocks are close...
                completed = time.time()
            else:
                duration = get_number(entry, 'duration')
                completed = started + duration
                completed /= 1000
            started /= 1000
            
            message, kind = {
                'SUCCESS': (_('Build finished successfully'),
                            ('build-successful',
                             'build-successful-alt')[self.alt_succ]),
                'UNSTABLE': (_('Build unstable'), 'build-unstable'),
                'ABORTED': (_('Build aborted'), 'build-aborted'),
                'INPROGRESS': (_('Build in progress'), 'build-inprogress'),
                }.get(result, (_('Build failed'), 'build-failed'))

            if self.use_desc:
                message = get_string(entry, 'description') or message

            name = get_string(entry, 'fullDisplayName')
            module = name[:name.rindex('#')]
            yield Build(name=name, module=module,
                        url=get_string(entry, 'url'),
                        author=get_string(entry, 'fullName'),
                        result=result, message=message, started=started, 
                        completed=completed, kind=kind)

    # IPermissionRequestor methods  

    def get_permission_actions(self):
        return ['BUILD_VIEW']

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'builds'

    def get_navigation_items(self, req):
        if req.perm.has_permission('BUILD_VIEW'):
            yield ('mainnav', 'builds',
                   tag.a(_("Build"),
                         href=self.nav_url or req.href('hudson-build'),
                         target=self.disp_tab and 'hudson' or None))

    # ITemplateProvider methods

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('HudsonTrac', resource_filename(__name__, 'htdocs'))]

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info.startswith('/hudson-build')

    def process_request(self, req):
        stop = datetime.now(req.tz)
        start = stop - timedelta(days=30)
        builds = self._extract_builds(self._get_info(start, stop))
        data = {'builds': list(builds)}
        add_script(req, 'HudsonTrac/hudsontrac.js')
        if req.locale is not None:
            add_script(req, 'HudsonTrac/hudsontrac/%s.js' % req.locale)
        add_stylesheet(req, 'HudsonTrac/hudsontrac.css')
        return 'hudson-build.html', data, None

    # ITimelineEventProvider methods

    def get_timeline_filters(self, req):
        if 'BUILD_VIEW' in req.perm:
            yield ('build', _('Hudson Builds'))

    def get_timeline_events(self, req, start, stop, filters):
        if 'build' not in filters or 'BUILD_VIEW' not in req.perm:
            return

        add_stylesheet(req, 'HudsonTrac/hudsontrac.css')

        # get and parse the build-info
        info = self._get_info(start, stop)
        for b in self._extract_builds(info):
            self.log.debug("Build: %r", b)
            yield b.kind, b.completed, b.author, b

    def render_timeline_event(self, context, field, event):
        b = event[3]
        if field == 'title':
            return tag_('Build %(name)s (%(result)s)', name=tag.em(b.name),
                        result=b.result.lower())
        elif field == 'description':
            elapsed = pretty_timedelta(b.started, b.completed)
            if b.kind == 'build-inprogress':
                return _("%(message)s since %(elapsed)s", message=b.message,
                         elapsed=elapsed)
            else:
                return _("%(message)s after %(elapsed)s", message=b.message,
                         elapsed=elapsed)
        elif field == 'url':
            return b.url
