Switching from a soft delete to deactivated flag. Essentially the same process, but allows delete endpoints to work as hard deletes with only admin access.
Deactivate will be a seperate update end point from the regular one, so that it can also only be called by elevated user.
Will deactivate manage the cascading? I think for now, no. Worried about orphaned entities with no relationships tying up the db.
Should post overwrite a deactivated enitiy? Don't think so, but update can and can't deactivate but will always reactivate if there is no conflict. if there is the whole update failss
