# -*- coding: utf-8 -*-
'''
'''
import os
import datetime
from sqlalchemy import or_
from ..model.record import _ScrapingRecords, _TransRecords
from ..utils.filehelper import checkFileExists, cleanFolderbyFilter, cleanFilebyFilter, cleanExtraMedia, cleanFolderWithoutSuffix, video_type
from .. import db


class ScrapingRecordService():

    def add(self, path) -> _ScrapingRecords:
        """ 优先查询已有数据
        存在则返回，不存在则新增
        """
        info = self.queryByPath(path)
        if not info:
            (filefolder, name) = os.path.split(path)
            if os.path.exists(path):
                size = os.path.getsize(path) >> 20
            else:
                size = 0
            info = _ScrapingRecords(name, path)
            info.srcsize = size
            db.session.add(info)
            db.session.commit()
        return info

    def queryByPath(self, value) -> _ScrapingRecords:
        return _ScrapingRecords.query.filter_by(srcpath=value).first()

    def queryLatest(self, value):
        infos = _ScrapingRecords.query.filter(_ScrapingRecords.srcpath.like("%" + value + "%")).all()
        return infos

    def queryByID(self, value) -> _ScrapingRecords:
        return _ScrapingRecords.query.filter_by(id=value).first()

    @staticmethod
    def deleteRecord(record: _ScrapingRecords, delsrc=False):
        basefolder = os.path.dirname(record.srcpath)
        if delsrc and os.path.exists(basefolder):
            srcname = os.path.basename(record.srcpath)
            srcfilter  = os.path.splitext(srcname)[0]
            cleanFilebyFilter(basefolder, srcfilter)
        if record.destpath != '':
            folder = os.path.dirname(record.destpath)
            if os.path.exists(folder) and basefolder != folder:
                name = os.path.basename(record.destpath)
                filter  = os.path.splitext(name)[0]
                if record.cdnum and record.cdnum > 0:
                    cleanFilebyFilter(folder, filter)
                else:
                    cleanFolderbyFilter(folder, filter)

    def deleteByIds(self, ids, delsrc=False):
        delrecords = []
        records = _ScrapingRecords.query.filter(_ScrapingRecords.id.in_(ids)).all()
        for record in records:
            self.deleteRecord(record, delsrc)
            delrecords.append(record.srcpath)
            db.session.delete(record)
        db.session.commit()
        return delrecords

    def cleanUnavailable(self):
        records = _ScrapingRecords.query.all()
        for i in records:
            if i.linktype == 0:
                if not os.path.exists(i.destpath):
                    self.deleteRecord(i, False)
                    db.session.delete(i)
            else:
                if not os.path.exists(i.srcpath) or not os.path.exists(i.destpath):
                    self.deleteRecord(i, False)
                    db.session.delete(i)
        db.session.commit()

    def deadtimetoMissingrecord(self) -> list:
        """ 源文件或目标文件不存在，全部删除
        """
        delrecords = []
        records = _ScrapingRecords.query.all()
        for i in records:
            # 排除忽略标记
            if i.status != 3:
                # 已标记deadtime，检查是否到期，进行删除
                if i.deadtime:
                    nowtime = datetime.datetime.now()
                    if nowtime > i.deadtime:
                        self.deleteRecord(i, True)
                        delrecords.append(i.srcpath)
                        db.session.delete(i)
                        continue
                # 0 转移 1 软链接 2 硬链接
                if i.linktype == 0:
                    # 转移必须是文件实体
                    if not os.path.exists(i.destpath):
                        if not i.deadtime or i.deadtime == '':
                            i.deadtime = datetime.datetime.now() + datetime.timedelta(days=3)
                    else:
                        # 曾经标记过，但现在已经恢复，则取消删除计划
                        if i.deadtime:
                            i.deadtime = None
                else:
                    if os.path.exists(i.srcpath) and checkFileExists(i.destpath):
                        # 曾经标记过，但现在已经恢复，则取消删除计划
                        if i.deadtime:
                            i.deadtime = None
                    else:
                        if not i.deadtime or i.deadtime == '':
                            i.deadtime = datetime.datetime.now() + datetime.timedelta(days=3)

        db.session.commit()
        return delrecords

    def editRecord(self, sid, status, scrapingname,
                   specifiedsource, specifiedurl,
                   cnsubtag, leaktag, uncensoredtag, hacktag, cdnum, deadtime):
        record = _ScrapingRecords.query.filter_by(id=sid).first()
        if record:
            record.status = status
            record.scrapingname = scrapingname
            record.specifiedsource = specifiedsource
            record.specifiedurl = specifiedurl
            record.cnsubtag = cnsubtag
            record.leaktag = leaktag
            record.uncensoredtag = uncensoredtag
            record.hacktag = hacktag
            if cdnum == '':
                cdnum = 0
            record.cdnum = int(cdnum)
            record.updatetime = datetime.datetime.now()
            if deadtime == '' and record.deadtime:
                record.deadtime = None
            db.session.commit()

    def commit(self):
        db.session.commit()

    def queryByPage(self, pagenum, pagesize, sortprop, sortorder, blur):
        """ 查询
        """
        blurparam = or_(_ScrapingRecords.srcname.like("%" + blur + "%"),
                        _ScrapingRecords.scrapingname.like("%" + blur + "%"),
                        _ScrapingRecords.destname.like("%" + blur + "%"))
        if sortprop == 'status':
            if sortorder == 'ascending':
                if blur:
                    infos = _ScrapingRecords.query.filter(blurparam).order_by(
                        _ScrapingRecords.status.asc()).paginate(pagenum, per_page=pagesize, error_out=False)
                else:
                    infos = _ScrapingRecords.query.order_by(_ScrapingRecords.status.asc()).paginate(
                        pagenum, per_page=pagesize, error_out=False)
            else:
                if blur:
                    infos = _ScrapingRecords.query.filter(blurparam).order_by(
                        _ScrapingRecords.status.desc()).paginate(pagenum, per_page=pagesize, error_out=False)
                else:
                    infos = _ScrapingRecords.query.order_by(_ScrapingRecords.status.desc()).paginate(
                        pagenum, per_page=pagesize, error_out=False)
        elif sortprop == 'cnsubtag':
            if sortorder == 'ascending':
                if blur:
                    infos = _ScrapingRecords.query.filter(blurparam).order_by(
                        _ScrapingRecords.cnsubtag.asc()).paginate(pagenum, per_page=pagesize, error_out=False)
                else:
                    infos = _ScrapingRecords.query.order_by(_ScrapingRecords.cnsubtag.asc()).paginate(
                        pagenum, per_page=pagesize, error_out=False)
            else:
                if blur:
                    infos = _ScrapingRecords.query.filter(blurparam).order_by(
                        _ScrapingRecords.cnsubtag.desc()).paginate(pagenum, per_page=pagesize, error_out=False)
                else:
                    infos = _ScrapingRecords.query.order_by(_ScrapingRecords.cnsubtag.desc()).paginate(
                        pagenum, per_page=pagesize, error_out=False)
        elif sortprop == 'deadtime':
            if sortorder == 'ascending':
                if blur:
                    infos = _ScrapingRecords.query.filter(blurparam).order_by(
                        _ScrapingRecords.deadtime.asc()).paginate(pagenum, per_page=pagesize, error_out=False)
                else:
                    infos = _ScrapingRecords.query.order_by(_ScrapingRecords.deadtime.asc()).paginate(
                        pagenum, per_page=pagesize, error_out=False)
            else:
                if blur:
                    infos = _ScrapingRecords.query.filter(blurparam).order_by(
                        _ScrapingRecords.deadtime.desc()).paginate(pagenum, per_page=pagesize, error_out=False)
                else:
                    infos = _ScrapingRecords.query.order_by(_ScrapingRecords.deadtime.desc()).paginate(
                        pagenum, per_page=pagesize, error_out=False)
        else:
            if sortorder == 'ascending':
                if blur:
                    infos = _ScrapingRecords.query.filter(blurparam).order_by(
                        _ScrapingRecords.updatetime.asc()).paginate(pagenum, per_page=pagesize, error_out=False)
                else:
                    infos = _ScrapingRecords.query.order_by(_ScrapingRecords.updatetime.asc(
                    )).paginate(pagenum, per_page=pagesize, error_out=False)
            else:
                if blur:
                    infos = _ScrapingRecords.query.filter(blurparam).order_by(
                        _ScrapingRecords.updatetime.desc()).paginate(pagenum, per_page=pagesize, error_out=False)
                else:
                    infos = _ScrapingRecords.query.order_by(_ScrapingRecords.updatetime.desc(
                    )).paginate(pagenum, per_page=pagesize, error_out=False)
        return infos


class TransRecordService():

    def add(self, path) -> _TransRecords:
        info = self.queryByPath(path)
        if not info:
            (filefolder, name) = os.path.split(path)
            size = os.path.getsize(path) >> 20
            info = _TransRecords(name, path)
            info.srcsize = size
            db.session.add(info)
            db.session.commit()
            return info
        return info

    def queryByID(self, value) -> _TransRecords:
        info = _TransRecords.query.filter_by(id=value).first()
        if not info:
            return None
        return info

    def queryByPath(self, value) -> _TransRecords:
        info = _TransRecords.query.filter_by(srcpath=value).first()
        if not info:
            return None
        return info

    def queryLatest(self, value):
        infos = _TransRecords.query.filter(_TransRecords.srcpath.like("%" + value + "%")).all()
        return infos

    def update(self, info: _TransRecords, softpath, destpath, status, 
                topfolder, secondfolder,
                isepisode, season, epnum, 
                renameTop_tag = False, renameSub_tag = False, deadtime=None):
        if info:
            info.linkpath = softpath
            info.destpath = destpath
            info.status = status
            if topfolder == '':
                topfolder = '.'
            if renameTop_tag and topfolder != '.':
                self.renameAllTop(info.srcfolder, info.topfolder, topfolder)
            info.topfolder = topfolder
            if isepisode:
                if renameSub_tag:
                    self.renameAllSeason(info.srcfolder, info.topfolder, info.secondfolder, info.season, season)
                else:
                    info.isepisode = True
                    info.season = season
                info.episode = epnum
                info.secondfolder = secondfolder
            else:
                info.isepisode = False
                if renameSub_tag:
                    self.renameAllSecond(info.srcfolder, info.topfolder, info.secondfolder, secondfolder)
                else:
                    info.secondfolder = secondfolder
            info.updatetime = datetime.datetime.now()
            if deadtime == '' and info.deadtime:
                info.deadtime = None
            db.session.commit()

    def queryByPage(self, pagenum, pagesize, sortprop, sortorder, blur):
        blurparam = or_(_TransRecords.srcname.like("%" + blur + "%"),
                        _TransRecords.destpath.like("%" + blur + "%"),
                        _TransRecords.topfolder.like("%" + blur + "%"))
        if sortprop == 'status':
            if sortorder == 'ascending':
                if blur:
                    infos = _TransRecords.query.filter(blurparam).order_by(
                        _TransRecords.status.asc()).paginate(pagenum, per_page=pagesize, error_out=False)
                else:
                    infos = _TransRecords.query.order_by(_TransRecords.status.asc()).paginate(
                        pagenum, per_page=pagesize, error_out=False)
            else:
                if blur:
                    infos = _TransRecords.query.filter(blurparam).order_by(
                        _TransRecords.status.desc()).paginate(pagenum, per_page=pagesize, error_out=False)
                else:
                    infos = _TransRecords.query.order_by(_TransRecords.status.desc()).paginate(
                        pagenum, per_page=pagesize, error_out=False)
        elif sortprop == 'deadtime':
            if sortorder == 'ascending':
                if blur:
                    infos = _TransRecords.query.filter(blurparam).order_by(
                        _TransRecords.deadtime.asc()).paginate(pagenum, per_page=pagesize, error_out=False)
                else:
                    infos = _TransRecords.query.order_by(_TransRecords.deadtime.asc()).paginate(
                        pagenum, per_page=pagesize, error_out=False)
            else:
                if blur:
                    infos = _TransRecords.query.filter(blurparam).order_by(
                        _TransRecords.deadtime.desc()).paginate(pagenum, per_page=pagesize, error_out=False)
                else:
                    infos = _TransRecords.query.order_by(_TransRecords.deadtime.desc()).paginate(
                        pagenum, per_page=pagesize, error_out=False)
        else:
            if sortorder == 'ascending':
                if blur:
                    infos = _TransRecords.query.filter(blurparam).order_by(
                        _TransRecords.updatetime.asc()).paginate(pagenum, per_page=pagesize, error_out=False)
                else:
                    infos = _TransRecords.query.order_by(_TransRecords.updatetime.asc()).paginate(
                        pagenum, per_page=pagesize, error_out=False)
            else:
                if blur:
                    infos = _TransRecords.query.filter(blurparam).order_by(
                        _TransRecords.updatetime.desc()).paginate(pagenum, per_page=pagesize, error_out=False)
                else:
                    infos = _TransRecords.query.order_by(_TransRecords.updatetime.desc()).paginate(
                        pagenum, per_page=pagesize, error_out=False)
        return infos

    @staticmethod
    def deleteRecord(record: _TransRecords, delsrc):
        basefolder = os.path.dirname(record.srcpath)
        if delsrc and os.path.exists(basefolder):
            srcname = os.path.basename(record.srcpath)
            srcfilter  = os.path.splitext(srcname)[0]
            cleanFilebyFilter(basefolder, srcfilter)
        if record.destpath != '':
            folder = os.path.dirname(record.destpath)
            if os.path.exists(folder) and basefolder != folder:
                name = os.path.basename(record.destpath)
                # 前缀匹配
                filter = os.path.splitext(name)[0]
                cleanFilebyFilter(folder, filter)
        if record.topfolder != '.':
            cleanfolder = os.path.dirname(record.destpath)
            if record.secondfolder:
                cleanfolder = os.path.dirname(cleanfolder)
            if os.path.exists(cleanfolder):
                cleanFolderWithoutSuffix(cleanfolder, video_type)

    def deleteByIds(self, ids, delsrc=False):
        delrecords = []
        records = _TransRecords.query.filter(_TransRecords.id.in_(ids)).all()
        for record in records:
            self.deleteRecord(record, delsrc)
            delrecords.append(record.srcpath)
            db.session.delete(record)
        db.session.commit()
        return delrecords

    def cleanUnavailable(self):
        records = _TransRecords.query.all()
        for i in records:
            if not os.path.exists(i.srcpath) or not os.path.exists(i.destpath):
                self.deleteRecord(i, False)
                db.session.delete(i)
        db.session.commit()

    def deadtimetoMissingrecord(self) -> list:
        delrecords = []
        records = _TransRecords.query.all()
        for i in records:
            # 忽略标记
            if i.status != 2:
                # 已标记deadtime，检查是否到期，进行删除
                if i.deadtime:
                    nowtime = datetime.datetime.now()
                    if nowtime > i.deadtime:
                        self.deleteRecord(i, True)
                        delrecords.append(i.srcpath)
                        db.session.delete(i)
                        continue
                # 0 软链接 1 硬链接
                if os.path.exists(i.srcpath) and checkFileExists(i.destpath):
                    if i.deadtime:
                        # 曾经标记过，但现在已经恢复，则取消删除计划
                        i.deadtime = None
                else:
                    if not i.deadtime or i.deadtime == '':
                        i.deadtime = datetime.datetime.now() + datetime.timedelta(days=3)
        db.session.commit()
        return delrecords

    def renameAllTop(self, srcfolder, top, new):
        records = _TransRecords.query.filter_by(srcfolder=srcfolder, topfolder=top).all()
        for single in records:
            if single.status != 1 and single.status != 2:
                single.topfolder = new
                single.updatetime = datetime.datetime.now()

    def renameAllSecond(self, srcfolder, top, second, new):
        records = _TransRecords.query.filter_by(srcfolder=srcfolder, topfolder=top, secondfolder=second).all()
        for single in records:
            if single.status != 1 and single.status != 2:
                single.secondfolder = new
                single.updatetime = datetime.datetime.now()

    def renameAllSeason(self, srcfolder, top, second, season, new):
        records = _TransRecords.query.filter_by(srcfolder=srcfolder, topfolder=top, 
                                                secondfolder=second, season=season).all()
        for single in records:
            if single.status != 1 and single.status != 2:
                single.isepisode = True
                single.season = new
                single.updatetime = datetime.datetime.now()


scrapingrecordService = ScrapingRecordService()
transrecordService = TransRecordService()
