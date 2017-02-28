# -*- coding: utf-8 -*-

"""
Modülün Açıklaması

__author__ : Çağatay Tengiz
__date__   : 16.03.2014
"""

from bottle import Bottle, request, abort, redirect
from sqlalchemy import exc

from utils_sa import formdata_to_sa
from utils import render, is_usr_admin
from i18n import _
import dbcon

subApp = Bottle()
__base_url = '/admin/usrgrp'
@subApp.route(__base_url)
@subApp.route(__base_url + '/<act>', method=['GET', 'POST'])
@subApp.route(__base_url + '/<act>/<ndx>', method=['GET', 'POST'])
def admin_usrgrp(db, act="lst", ndx=0):

    if not is_usr_admin(db):
        abort(403, _('You are not granted to access this page'))

    atmp = request.urlparts.path.split('/')[2]
    apth = "/admin/%s" % atmp

    atbl = dbcon.UsrGrp
    brd = [{"link": apth, "defi": _("Groups")}]

    if request.method == 'GET':

        if act == "lst":
            alst = db.query(atbl).order_by(atbl.id).all()
            return render('%s_list.tpl' % atmp, alst=alst, breadcumb=brd, base_url=__base_url)

        elif act == "edit":
            brd.append({"link": "", "defi": _("Edit")})

            arec = db.query(atbl).filter(atbl.id == ndx).first()
            if arec:
                return render('%s_edit.tpl' % atmp, arec=arec, breadcumb=brd, base_url=__base_url)
            else:
                abort(404, _('No record found'))

        elif act == "add":
            brd.append({"link": "", "defi": _("New")})
            arec = atbl()
            arec.id = 0

            return render('%s_edit.tpl' % atmp, arec=arec, breadcumb=brd)

        elif act == "del":
            data = db.query(atbl).filter(atbl.id == ndx).first()
            if not data:
                abort(404, _("No record to delete"))

            db.delete(data)
            redirect(apth)
        else:
            abort(404, _('Operation type %s is not supported')% (act, ))

    else:
        data = request.POST

        #todo: bu kaydetme işlemini jenerik hale getirelim !
        if act == "add":
            arec = atbl()
            db.add(arec)
        else:
            arec = db.query(atbl).filter(atbl.id == ndx).first()

        if act in ['add', 'edit']:
            formdata_to_sa(data, atbl, arec)

            new_members = []
            _nro = 0
            if data['members']:
                for k in data['members'].split(','):
                    _nro += 1
                    new_members.append(
                        #todo: statu_id is hard coded. Initial value should be read from a setting value
                        dbcon.UsrGrp_Usr(usr_id=int(k), usrgrp_id=arec.id)
                    )

            arec.members = new_members

            try:
                db.commit()

                #todo: burada ileride json dönmeliyiz !
                redirect(apth)
            except exc.SQLAlchemyError as err:
                db.rollback()
                abort(500,
                      _("Error in processing DB operation.<br\>Please try again! DB Error Msg:<br/>%s") % err)