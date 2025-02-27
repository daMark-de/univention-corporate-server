<!--
  Copyright 2021 Univention GmbH

  https://www.univention.de/

  All rights reserved.

  The source code of this program is made available
  under the terms of the GNU Affero General Public License version 3
  (GNU AGPL V3) as published by the Free Software Foundation.

  Binary versions of this program provided by Univention to you as
  well as other copyrighted, protected or trademarked materials like
  Logos, graphics, fonts, specific documentations and configurations,
  cryptographic keys etc. are subject to a license agreement between
  you and Univention and not subject to the GNU AGPL V3.

  In the case you use this program under the terms of the GNU AGPL V3,
  the program is provided in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
  GNU Affero General Public License for more details.

  You should have received a copy of the GNU Affero General Public
  License with the Debian GNU/Linux or Univention distribution in file
  /usr/share/common-licenses/AGPL-3; if not, see
  <https://www.gnu.org/licenses/>.
-->
<script>
import { mapGetters } from 'vuex';
import { DragType } from '@/store/modules/dragndrop';

const draggableMixin = {
  computed: {
    ...mapGetters({
      inDragnDropMode: 'dragndrop/inDragnDropMode',
      inKeyboardDragnDropMode: 'dragndrop/inKeyboardDragnDropMode',
      dragndropId: 'dragndrop/getId',
      editMode: 'portalData/editMode',
    }),
    isDraggable() {
      if (!this.editMode) {
        return false;
      }
      switch (this.$options.name) {
        case 'PortalTile':
          return !this.minified;
        case 'PortalFolder':
          return !this.inModal;
        case 'PortalCategory':
          return !this.virtual;
        case 'TileAdd':
        default:
          return false;
      }
    },
    isBeingDragged() {
      if (!this.isDraggable) {
        return false;
      }
      return this.dragndropId.layoutId === this.layoutId;
    },
    showMoveButtonWhileDragging() {
      return this.inKeyboardDragnDropMode ? this.isBeingDragged : true;
    },
    showEditButtonWhileDragging() {
      return !this.inKeyboardDragnDropMode;
    },
    canDragEnter() {
      if (this.forFolder !== undefined) {
        // TileAdd
        return true;
      }
      return this.isDraggable;
    },
  },
  methods: {
    draggedType() {
      let draggedType = 'tile';
      if (this.$options.name === 'PortalCategory') {
        draggedType = 'category';
      }
      return draggedType;
    },
    dragKeyboardClick() {
      if (this.isBeingDragged) {
        this.$store.dispatch('portalData/saveLayout');
      } else {
        this.dragstart(null, 'keyboard');
      }
    },
    dragKeyboardDirection(evt, direction) {
      if (!this.inDragnDropMode) {
        return;
      }
      evt.preventDefault();

      this.$store.dispatch('dragndrop/lastDir', direction);
      this.$store.dispatch('portalData/changeLayoutDirection', {
        fromId: this.layoutId,
        direction,
      });
      this.$nextTick(() => {
        this.handleDragFocus(evt.target, direction);
      });
    },
    handleDragFocus(elem, direction) {
      if (this.isBeingDragged) {
        const rect = elem.getBoundingClientRect();
        const offset = 200;
        if (rect.top !== 0) {
          if (direction === 'down' || direction === 'right') {
            if (rect.top + offset > window.innerHeight) {
              window.scrollBy(0, rect.top - window.innerHeight + offset);
            }
          }
          if (direction === 'up' || direction === 'left') {
            if (rect.top - offset < 0) {
              window.scrollBy(0, rect.top - offset);
            }
          }
        }
        // @ts-ignore
        elem.focus();
      }
    },
    handleTabWhileMoving() {
      if (this.isBeingDragged) {
        this.$store.dispatch('portalData/saveLayout');
      }
    },
    dragstart(evt, dragType) {
      if (!this.isDraggable) {
        return;
      }

      this.$store.dispatch('dragndrop/startDragging', {
        layoutId: this.layoutId,
        draggedType: this.draggedType(),
        dragType,
        saveOriginalLayout: true,
      });
    },
    dragenter(evt) {
      if (!this.canDragEnter) {
        evt.preventDefault();
        return;
      }

      const data = this.$store.getters['dragndrop/getId'];
      if (data.draggedType !== this.draggedType()) {
        return;
      }

      const toIsAddTile = this.$options.name === 'TileAdd';
      const toId = toIsAddTile ? this.superLayoutId : this.layoutId;
      const position = toIsAddTile ? -1 : null;
      this.$store.dispatch('portalData/changeLayout', {
        fromId: data.layoutId,
        toId,
        position,
      });
    },
    dragend(evt) {
      // if dragend is called via esc key we want to stop
      // the event (if we are in drag mode)
      if (this.inDragnDropMode) {
        evt?.preventDefault();
        evt?.stopImmediatePropagation();
      }
      this.$store.dispatch('dragndrop/cancelDragging');
    },
  },
};

export default draggableMixin;
</script>
<style>
</style>
